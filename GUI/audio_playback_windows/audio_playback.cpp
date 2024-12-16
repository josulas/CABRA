#include <audioclient.h>
#include <mmdeviceapi.h>
#include <functiondiscoverykeys_devpkey.h>
#include <avrt.h>
#include <windows.h>
#include <stdio.h>
#include <time.h>
#include <iostream>
using namespace std;

// Comment all printf statements as wished
#if 0
    #define printf(...) ((void)0)
#endif


#define REFTIMES_PER_SEC  10000000
#define REFTIMES_PER_MILLISEC  10000
#define EXIT_ON_ERROR(hres)  \
              if (FAILED(hres)) { goto Exit; }
#define SAFE_RELEASE(punk)  \
              if ((punk) != NULL)  \
                { (punk)->Release(); (punk) = NULL; }
#define CHECK_HR(hr, msg) if (FAILED(hr)) { printf("%s failed: 0x%08x\n", msg, hr); goto cleanup; }

#define MAX_PATH_LENGTH 256

// FILE LOAD
FILE *file;
long fileSize;
char header[44]; // WAV headers are typically 44 bytes
HWAVEOUT hWaveOut;
WAVEFORMATEX wfx;
unsigned char *audioData;


// WASAPI playback
const CLSID CLSID_MMDeviceEnumerator = __uuidof(MMDeviceEnumerator);
const IID IID_IMMDeviceEnumerator = __uuidof(IMMDeviceEnumerator);
const IID IID_IAudioClient = __uuidof(IAudioClient);
const IID IID_IAudioRenderClient = __uuidof(IAudioRenderClient);
HRESULT hr;
REFERENCE_TIME hnsRequestedDuration = 25 * REFTIMES_PER_MILLISEC;
REFERENCE_TIME hnsActualDuration;
IMMDeviceEnumerator *pEnumerator = NULL;
IMMDevice *pDevice = NULL;
IAudioClient *pAudioClient = NULL;
IAudioRenderClient *pRenderClient = NULL;
WAVEFORMATEX *pwfx = NULL;
UINT32 bufferFrameCount;
UINT32 numFramesAvailable;
UINT32 numFramesPadding;
UINT32 remainingFrames;
BYTE *pData;
DWORD flags = 0;
DWORD taskIndex = 0;
HANDLE hTask = NULL;
HANDLE hEvent = NULL;


// Define the audio source class
class WavAudioSource{
    WAVEFORMATEX *pwfx;
    WAVEFORMATEX *pwfxClient;
    BYTE *pStreamData;
    UINT32 dataSize, position, remainingData;
public:
    void SetData(BYTE *pData, UINT32 size, WAVEFORMATEX *pwfx){
        pStreamData = pData;
        dataSize = size;
        pwfxClient = pwfx;
        position = 0;
        remainingData = size;
    }
    HRESULT LoadData(UINT32 bufferFrameCount, BYTE *pData, DWORD *flags);
    HRESULT SetFormat(WAVEFORMATEX *pwfx){
        pwfxClient = pwfx;
        if (pwfxClient == NULL) {
            return E_POINTER;
        }
        if (
            pwfxClient->nChannels != pwfx->nChannels ||
            pwfxClient->nSamplesPerSec != pwfx->nSamplesPerSec ||
            pwfxClient->wBitsPerSample != pwfx->wBitsPerSample ||
            pwfxClient->nBlockAlign != pwfx->nBlockAlign ||
            pwfxClient->nAvgBytesPerSec != pwfx->nAvgBytesPerSec) {
            return E_INVALIDARG;
        }
        return S_OK;
    }
    UINT32 GetRemainingFrames(UINT32 *pFrames){
        if (pFrames == NULL) {
            return E_POINTER;
        }
        *pFrames = remainingData / pwfxClient->nBlockAlign;
        return S_OK;
    }
    void Reset(){
        position = 0;
        remainingData = dataSize;
    }
};


// Function prototypes
HRESULT PrepareAudioStream(WavAudioSource *pMySource);
HRESULT PlayAudioStream(WavAudioSource *pMySource);
void safeExit();
int loadWavFile(const char *file_path);
void SwapStereoChannels(unsigned char *audioData, WAVEFORMATEX *wfex, size_t totalFrames);


// Main function
int main() {
    // CPU affinity
    WavAudioSource pMySource;
    HANDLE hProcess = GetCurrentProcess();
    bool path_set = false;
    bool audio_loaded = false;
    char audio_file_path[MAX_PATH_LENGTH];

    // Set the process priority to "High"
    if (!SetPriorityClass(hProcess, HIGH_PRIORITY_CLASS)) {
        return 1;
    }

    // Set timing resolution to 1 ms
    timeBeginPeriod(1);
    // Initialize COM
    hr = CoInitialize(NULL);
    if FAILED(hr) {
        safeExit();
        return 1;
    }
    
    bool unrecoverable_error = false;
    char command[MAX_PATH_LENGTH];
    while (fgets(command, sizeof(command), stdin)) {
        // Remove newline from the command
        command[strcspn(command, "\n")] = 0;
        if (strcmp(command, "E") == 0) {
            // End command, break the loop
            break;
        } else if (strcmp(command, "L") == 0) {
            // Load audio command
            if (path_set) {
                if (loadWavFile(audio_file_path)) {
                    audio_loaded = true;
                    printf("D\n"); // Acknowledge audio loading
                    fflush(stdout);
                } else {
                    printf("E\n"); // Error signal
                    fflush(stdout);
                    // Continue, since the error is recoverable
                }
                pMySource.SetData(audioData, fileSize - 44, &wfx);
                if (FAILED(PrepareAudioStream(&pMySource))) {
                    safeExit();
                    printf("E\n"); // Error signal
                    fflush(stdout);
                    unrecoverable_error = true;
                    break; // Cannot recover from this error
                }
            } else {
                printf("E\n"); // Error signal
                fflush(stdout);
            }
        } else if (strcmp(command, "P") == 0) {
            // Start playback command
            if (!audio_loaded) {
                printf("E\n"); // Error signal
                fflush(stdout);
            } else {
                 if(FAILED(PlayAudioStream(&pMySource))){
                    safeExit();
                    printf("E\n"); // Error signal
                    fflush(stdout);
                    unrecoverable_error = true;
                    break; // Cannot recover from this error
                 }
            }
        } else {
            // Assume any other input is the path
            strncpy_s(audio_file_path, command, MAX_PATH_LENGTH);
            path_set = true;
            audio_loaded = false;
            if (audioData) {
                free(audioData);
                audioData = NULL;
            }
            printf("U\n"); // Acknowledge path reception
            fflush(stdout);
        }
    }
    // Cleanup
    CoUninitialize();
    timeEndPeriod(1);
    if (audioData) {
        free(audioData);
    }
    return unrecoverable_error ? 1 : 0;
}


int loadWavFile(const char *file_path) {
    UINT32 totalFrames;

    fopen_s(&file, file_path, "rb");
    if (!file) {
        fprintf(stderr, "Failed to open file: %s\n", file_path);
        return 0;
    }
    // Load the WAV header to understand the audio format
    fread(header, sizeof(char), 44, file);

    // Read audio data
    fseek(file, 0, SEEK_END);
    fileSize = ftell(file);
    rewind(file);

    audioData = (unsigned char *)malloc(fileSize - 44);  // Allocate memory for the audio data (skipping header)
    if (!audioData) {
        perror("Memory allocation failed");
        fclose(file);
        return 0;
    }

    fread(audioData, sizeof(char), fileSize - 44, file);  // Read audio data into the buffer
    fclose(file);

    // Set the WAV format (adjust as needed)
    wfx.wFormatTag = ((unsigned char) header[20]) | (((unsigned char) header[21]) << 8);
    // Channels (2 bytes, little-endian)
    wfx.nChannels = ((unsigned char) header[22]) | (((unsigned char) header[23]) << 8);
    // Sample rate (4 bytes, little-endian)
    wfx.nSamplesPerSec = 
    ((unsigned char) header[24]) | 
    (((unsigned char) header[25]) << 8) | 
    (((unsigned char) header[26]) << 16) | 
    (((unsigned char) header[27]) << 24);
    // Bits per sample (2 bytes, little-endian)
    wfx.wBitsPerSample = ((unsigned char) header[34]) | (((unsigned char) header[35]) << 8);
    // Derived values
    wfx.nBlockAlign = ((unsigned char) header[32]) | (((unsigned char) header[33]) << 8);
    wfx.nAvgBytesPerSec = 
    ((unsigned char) header[28]) | 
    (((unsigned char) header[29]) << 8) | 
    (((unsigned char) header[30]) << 16) | 
    (((unsigned char) header[31]) << 24);
    wfx.cbSize = 0;

    totalFrames = (fileSize - 44) / wfx.nBlockAlign;
    SwapStereoChannels(audioData, &wfx, totalFrames);
    
    return 1; // Success
}


HRESULT WavAudioSource::LoadData(UINT32 numFramesRequested, BYTE *pData, DWORD *flags) {
    UINT32 bytesRequested = numFramesRequested * pwfxClient->nBlockAlign;
    if (remainingData > 0) {
        UINT32 bytesAvailable = remainingData;
        UINT32 bytesToCopy = min(bytesRequested, bytesAvailable);

        // Copy available audio data
        memcpy(pData, pStreamData + position, bytesToCopy);

        // Zero-fill the rest if there's any unused buffer space
        if (bytesToCopy < bytesRequested) {
            memset(pData + bytesToCopy, 0, bytesRequested - bytesToCopy);
        }

        // Update the stream pointer and remaining data size
        position += bytesToCopy;
        remainingData -= bytesToCopy;
    } else {
        // No data left; fill the buffer with silence
        memset(pData, 0, bytesRequested);
        *flags = AUDCLNT_BUFFERFLAGS_SILENT;
    }
    return S_OK;
}

HRESULT PrepareAudioStream(WavAudioSource *pMySource){
    hEvent = CreateEvent(NULL, FALSE, FALSE, NULL);
    if (FAILED(hr)){
        safeExit();
        return hr;
    }

    hr = CoCreateInstance(
           CLSID_MMDeviceEnumerator, NULL,
           CLSCTX_ALL, IID_IMMDeviceEnumerator,
           (void**)&pEnumerator);
    if (FAILED(hr)){
        safeExit();
        return hr;
    }

    hr = pEnumerator->GetDefaultAudioEndpoint(
                        eRender, eConsole, &pDevice);
    if (FAILED(hr)){
        safeExit();
        return hr;
    }

    hr = pDevice->Activate(
                    IID_IAudioClient, CLSCTX_ALL,
                    NULL, (void**)&pAudioClient);
    if (FAILED(hr)){
        safeExit();
        return hr;
    }

    hr = pAudioClient->GetMixFormat(&pwfx);
    if (FAILED(hr)){
        safeExit();
        return hr;
    }
    pwfx->wFormatTag = WAVE_FORMAT_PCM;
    pwfx->cbSize = 0;

    hr = pAudioClient->Initialize(
                         AUDCLNT_SHAREMODE_SHARED,
                         0,
                         hnsRequestedDuration,
                         0,
                         pwfx,
                         NULL);
    if (FAILED(hr)){
        safeExit();
        return hr;
    }

    // Tell the audio source which format to use.
    hr = pMySource->SetFormat(pwfx);
    if (FAILED(hr)){
        safeExit();
        return hr;
    }

    // Get the actual size of the allocated buffer.
    hr = pAudioClient->GetBufferSize(&bufferFrameCount);
    if (FAILED(hr)){
        safeExit();
        return hr;
    }

    hr = pAudioClient->GetService(
                         IID_IAudioRenderClient,
                         (void**)&pRenderClient);
    if (FAILED(hr)){
        safeExit();
        return hr;
    }
    return hr;
}


HRESULT PlayAudioStream(WavAudioSource *pMySource)
{
    // Grab the entire buffer for the initial fill operation, or what is needed.
    pMySource->GetRemainingFrames(&remainingFrames);
    hr = pRenderClient->GetBuffer(bufferFrameCount, &pData);
    if (FAILED(hr)){
        safeExit();
        return hr;
    }

    // Load the initial data into the shared buffer.
    hr = pMySource->LoadData(bufferFrameCount, pData, &flags);
    if (FAILED(hr)){
        safeExit();
        return hr;
    }

    // Release the buffer.
    hr = pRenderClient->ReleaseBuffer(bufferFrameCount, flags);
    if (FAILED(hr)){
        safeExit();
        return hr;
    }

    // Calculate the actual duration of the allocated buffer.
    hnsActualDuration = (double)REFTIMES_PER_SEC *
                        bufferFrameCount / pwfx->nSamplesPerSec;

    // Start playing.
    hTask = AvSetMmThreadCharacteristics("Low Latency", &taskIndex);
    hr = pAudioClient->Start();  
    printf("S\n"); // Start signal
    fflush(stdout);
    if (FAILED(hr)){
        safeExit();
        return hr;
    }

    // Each loop fills about half of the shared buffer.
    while (1)
    {
        pMySource->GetRemainingFrames(&remainingFrames);
        if (remainingFrames == 0) {
            break;
        }
        // Sleep for half the buffer duration.
        Sleep((DWORD)(hnsActualDuration/REFTIMES_PER_MILLISEC/2));

        // See how much buffer space is available.
        hr = pAudioClient->GetCurrentPadding(&numFramesPadding);
        if FAILED(hr){ 
            safeExit();
            return hr;
        }

        numFramesAvailable = bufferFrameCount - numFramesPadding;

        // Grab all the available space in the shared buffer.
        hr = pRenderClient->GetBuffer(numFramesAvailable, &pData);
        if FAILED(hr){ 
            safeExit();
            return hr;
        }

        // Get next 1/2-second of data from the audio source.
        hr = pMySource->LoadData(numFramesAvailable, pData, &flags);
        if FAILED(hr){ 
            safeExit();
            return hr;
        }

        hr = pRenderClient->ReleaseBuffer(numFramesAvailable, flags);
        if FAILED(hr){ 
            safeExit();
            return hr;
        }
    }
    
    do{
        WaitForSingleObject(hEvent, (DWORD)(1));
        hr = pAudioClient->GetCurrentPadding(&numFramesPadding);
        if FAILED(hr){ 
            safeExit();
            return hr;
        }
    } while (numFramesPadding > 0);

    // Stop playing.
    hr = pAudioClient->Stop();  // Stop playing.
    if (FAILED(hr)){
        safeExit();
        return hr;
    }

    // Explicitly reset the audio client
    hr = pAudioClient->Reset();
    if (FAILED(hr)){
        safeExit();
        return hr;
    }

    // Reset the thread priority back to normal.
    AvRevertMmThreadCharacteristics(hTask);

    // Reset the audio source.
    pMySource->Reset();

    printf("F\n"); // Start signal
    fflush(stdout);

    return hr; // S_OK
}

void safeExit(){
    CoTaskMemFree(pwfx);
    SAFE_RELEASE(pEnumerator)
    SAFE_RELEASE(pDevice)
    SAFE_RELEASE(pAudioClient)
    SAFE_RELEASE(pRenderClient)
    if (hEvent != NULL) CloseHandle(hEvent);
}


// Function to swap left and right channels
void SwapStereoChannels(unsigned char* audioData, WAVEFORMATEX* wfex, size_t totalFrames) {
    // Ensure it's stereo and PCM
    if (wfex->nChannels != 2 || wfex->wFormatTag != WAVE_FORMAT_PCM) {
        printf("The audio format is not stereo PCM. No swapping will be done.\n");
        return;
    }

    // Calculate bytes per sample
    size_t bytesPerSample = wfex->wBitsPerSample / 8;
    if (bytesPerSample < 1) {
        printf("Invalid bits per sample.\n");
        return;
    }

    // Calculate the size of one frame (two channels, so 2 * bytesPerSample)
    size_t frameSize = 2 * bytesPerSample;

    // Swap left and right channels for each frame
    for (size_t i = 0; i < totalFrames; ++i) {
        // Pointer to the current frame
        uint8_t* frame = audioData + i * frameSize;

        // Swap left and right channels
        for (size_t j = 0; j < bytesPerSample; ++j) {
            uint8_t temp = frame[j];
            frame[j] = frame[bytesPerSample + j];
            frame[bytesPerSample + j] = temp;
        }
    }
}


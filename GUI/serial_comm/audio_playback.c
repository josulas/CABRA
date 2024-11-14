#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <io.h>
#include <windows.h>
#include <mmsystem.h>
#pragma comment(lib, "winmm.lib")

#define MAX_PATH_LENGTH 256

char audio_file_path[MAX_PATH_LENGTH];
int path_set = 0;
int audio_loaded = 0;
double cpu_time_used;
char *audio_data = NULL;
DWORD audio_data_size = 0;

int load_audio_into_memory(const char *file_path) {
    FILE *file = fopen(file_path, "rb");
    if (!file) {
        fprintf(stderr, "Failed to open file: %s\n", file_path);
        return 0;
    }
    // Get file size
    fseek(file, 0, SEEK_END);
    audio_data_size = ftell(file);
    fseek(file, 0, SEEK_SET);
    // Allocate memory and read the file
    audio_data = (char *)malloc(audio_data_size);
    if (!audio_data) {
        fprintf(stderr, "Failed to allocate memory\n");
        fclose(file);
        return 0;
    }
    fread(audio_data, 1, audio_data_size, file);
    fclose(file);
    return 1;
}


// Simulate playing the audio (could be replaced with actual playback code)
void play_audio() {
    // if (PlaySound(audio_file_path, NULL, SND_FILENAME)){
    if (PlaySound(audio_data, NULL, SND_MEMORY | SND_ASYNC)) {
        printf("F\n"); // Finished playing signal
        fflush(stdout);
    } else {
        printf("E\n"); // Error signal
        fflush(stdout);
    }
}

int main() {
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
                if (load_audio_into_memory(audio_file_path)) {
                    audio_loaded = 1;
                    printf("D\n"); // Acknowledge audio loading
                    fflush(stdout);
                } else {
                    printf("E\n"); // Error signal
                    fflush(stdout);
                }
            } else {
                printf("E\n"); // Error signal
                fflush(stdout);
            }
        } else if (strcmp(command, "S") == 0) {
            // Start playback command
            if (!audio_loaded) {
                printf("E\n"); // Error signal
                fflush(stdout);
            } else {
                play_audio();
            }
        } else {
            // Assume any other input is the path
            strncpy(audio_file_path, command, MAX_PATH_LENGTH);
            path_set = 1;
            audio_loaded = 0;
            if (audio_data) {
                free(audio_data);
                audio_data = NULL;
                audio_data_size = 0;
            }
            printf("U\n"); // Acknowledge path reception
            fflush(stdout);
        }
    }
    return 0;
}

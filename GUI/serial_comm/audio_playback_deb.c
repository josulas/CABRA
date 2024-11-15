#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ao/ao.h>
#include <sndfile.h>

#define MAX_PATH_LENGTH 256

char audio_file_path[MAX_PATH_LENGTH];
int path_set = 0;
int audio_loaded = 0;
char *audio_data = NULL;
sf_count_t audio_data_size = 0;
SF_INFO sfinfo;
SNDFILE *sndfile = NULL;

int load_audio_into_memory(const char *file_path) {
    sndfile = sf_open(file_path, SFM_READ, &sfinfo);
    if (!sndfile) {
        fprintf(stderr, "Failed to open file: %s\n", file_path);
        return 0;
    }
    audio_data_size = sfinfo.frames * sfinfo.channels * sizeof(short);
    audio_data = (char *)malloc(audio_data_size);
    if (!audio_data) {
        fprintf(stderr, "Failed to allocate memory\n");
        sf_close(sndfile);
        return 0;
    }
    sf_readf_short(sndfile, (short *)audio_data, sfinfo.frames);
    sf_close(sndfile);
    return 1;
}

void play_audio() {
    ao_device *device;
    ao_sample_format format;
    int default_driver;

    ao_initialize();
    default_driver = ao_default_driver_id();
    memset(&format, 0, sizeof(format));
    format.bits = 16;
    format.channels = sfinfo.channels;
    format.rate = sfinfo.samplerate;
    format.byte_format = AO_FMT_NATIVE;

    device = ao_open_live(default_driver, &format, NULL);
    if (device == NULL) {
        fprintf(stderr, "Error opening device.\n");
        return;
    }

    ao_play(device, audio_data, audio_data_size);
    ao_close(device);
    ao_shutdown();
}

int main() {
    char command[MAX_PATH_LENGTH];
    while (fgets(command, sizeof(command), stdin)) {
        command[strcspn(command, "\n")] = 0;
        if (strcmp(command, "E") == 0) {
            break;
        } else if (strcmp(command, "L") == 0) {
            if (path_set) {
                if (load_audio_into_memory(audio_file_path)) {
                    audio_loaded = 1;
                    printf("D\n");
                    fflush(stdout);
                } else {
                    printf("E\n");
                    fflush(stdout);
                }
            } else {
                printf("E\n");
                fflush(stdout);
            }
        } else if (strcmp(command, "S") == 0) {
            if (!audio_loaded) {
                printf("E\n");
                fflush(stdout);
            } else {
                play_audio();
            }
        } else {
            strncpy(audio_file_path, command, MAX_PATH_LENGTH);
            path_set = 1;
            audio_loaded = 0;
            if (audio_data) {
                free(audio_data);
                audio_data = NULL;
                audio_data_size = 0;
            }
            printf("U\n");
            fflush(stdout);
        }
    }
    return 0;
}
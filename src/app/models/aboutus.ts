export interface Aboutus {
    version: {
        current_release: string,
        ale_repository_build_available: string,
        build: string,
        "vna_rainbow_status": string,
    },
    system: {
        hostname: string,
        ip_address: string,
        "mac_address": string,
        operatingsystem: string,
        "version_distribution": string,
        architecture: string,
        total_memory: string,
        free_memory: string,
        cpu: string,
    },
    hard_disk: {
        total_memory: string,
        free_memory: string,
        local_disk: string
    }
}





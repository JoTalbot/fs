/*
 * Minimal FreeBSD Capsicum workload launcher.
 *
 * The launcher opens the target before entering capability mode, reduces the
 * executable descriptor to the minimum rights needed for fexecve(), enters
 * capability mode, verifies kernel state with cap_getmode(), proves that
 * global filesystem lookup is blocked, and finally replaces itself with the
 * target through fexecve().
 *
 * It intentionally accepts no shell command string and never expands
 * privileges. The target path is resolved before cap_enter(), after which
 * global namespace access is no longer available to the workload.
 */
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/capsicum.h>
#include <unistd.h>

static int fail(const char *what) {
    fprintf(stderr, "capsicum-helper-error:%s:%d\n", what, errno);
    return 126;
}

int main(int argc, char **argv, char **envp) {
    if (argc < 2) {
        fprintf(stderr, "usage: capsicum_exec TARGET [ARG ...]\n");
        return 64;
    }

    int fd = open(argv[1], O_RDONLY);
    if (fd < 0) {
        return fail("open-target");
    }

    cap_rights_t rights;
    cap_rights_init(&rights, CAP_READ, CAP_FEXECVE);
    if (cap_rights_limit(fd, &rights) < 0) {
        int result = fail("cap-rights-limit");
        close(fd);
        return result;
    }

    if (cap_enter() < 0) {
        int result = fail("cap-enter");
        close(fd);
        return result;
    }

    unsigned int mode = 0;
    if (cap_getmode(&mode) < 0 || mode == 0) {
        int result = fail("cap-getmode");
        close(fd);
        return result;
    }

    fprintf(stderr, "capsicum-capability-mode-entered\n");
    fprintf(stderr, "capsicum-capability-mode-verified\n");

    errno = 0;
    int blocked_fd = open("/etc/passwd", O_RDONLY);
    if (blocked_fd >= 0) {
        close(blocked_fd);
        errno = 0;
        return fail("global-namespace-not-blocked");
    }
    if (errno != ECAPMODE && errno != ENOTCAPABLE) {
        return fail("unexpected-global-namespace-error");
    }
    fprintf(stderr, "capsicum-global-namespace-blocked\n");

    fexecve(fd, &argv[1], envp);
    return fail("fexecve");
}

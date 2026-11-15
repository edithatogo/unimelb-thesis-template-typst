# Verifier process timeouts

`scripts/verify.py` gives each external compile, query and PDF-tool command
a 60-second execution budget. If that budget expires, the command fails and
receives a separate five-second cleanup budget. A timeout remains a failure
when the parent has already exited successfully but a descendant still holds
its output pipes open.

On POSIX systems, the runner starts each command in a new session and sends
`SIGKILL` to that command's process group on timeout. Cleanup uses one shared
deadline for collecting output and reaping the immediate child. The runner
records the attempted command, working directory, controlled environment,
budgets, isolation mode, elapsed time, actual exit status, output hashes, log
hash and timeout or cleanup diagnostic before raising a verification error.
An expected nonzero exit is accepted only when the command completes within
its budget and returns the declared status.

## Process probes

The maintenance suite runs five test methods containing six real command
invocations:

1. A normal command and an expected nonzero command preserve stdout, stderr,
   exit status and their evidence hashes.
2. An unexpected nonzero command fails with its original diagnostics retained.
3. A missing executable fails with the attempted command and start error retained.
4. A running parent and its sleeping child are stopped after the command budget.
5. An exited parent cannot hide a sleeping child that retains the output pipes.

The two descendant probes require Linux `/proc` and pidfds so they can observe
actual process state/start time and bind cleanup signalling to the owned
process. They explicitly skip when that capability is absent. The other three tests remain portable. A probe verifies that the child
really started before checking that it stopped; a missing child is not a pass.
Test cleanup opens a pidfd and checks the recorded start time before signalling
any leftover child; a reused numeric PID is not treated as the original child.

The tests temporarily use a one-second execution budget while preserving the
production five-second cleanup budget. This test-only override does not change
the 60-second compile/PDF allowance. Run them with:

```sh
python -m unittest discover -s tests/maintenance \
  -p 'test_verifier_processes.py' -v
```

`make verify` also discovers these tests. Logs and observations are retained
under `build/verifier-watchdog/` and uploaded with the existing verification
artifact. The unittest outcome determines pass or failure; a teardown record
or a successful cleanup action does not turn a failed assertion into a pass.

## Boundaries

The POSIX process-group rule covers descendants that remain in that group.
A child that deliberately creates a new session is outside that containment
boundary. Such a child can still cause the pipe-collection cleanup deadline
to fail, but this implementation does not claim to terminate arbitrary detached
process trees. A quiet background child whose parent and output pipes have
already completed is outside these timeout probes.

On non-POSIX systems the fallback terminates the direct child. Descendant
termination and inherited-pipe cleanup on Windows remain unqualified. This
work does not introduce Windows job objects or claim equivalent behavior.

Operating-system process creation and artifact writes are outside the measured
communication/cleanup intervals. The existing hosted job timeout supplies the
outer limit. Process tests do not establish all TST-03 requirements, offline
replay, artifact provenance or whole-repository line/branch coverage.

# Turns `gh run view --job <id> --log` output into clean logs and terminal-style screenshots.
import html
import os
import re
import subprocess

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
ANSI = re.compile(r"\x1b\[[0-9;]*m|\^\[\[[0-9;]*m")
TS = re.compile(r"^\d{4}-\d\d-\d\dT[\d:.]+Z ?")
NOISE = re.compile(r"##\[(group|endgroup)\]|^(shell|env|with):|^  \S+: |^\s*$|pythonLocation|_ROOT_DIR|LD_LIBRARY"
                   r"|^[0-9a-f]{12}: (Pulling|Waiting|Verifying|Download|Pull complete)")


def clean(raw, steps, keep=None):
    """Keep only the given steps; drop timestamps, colour codes and the echoed script lines."""
    out, last, step = [], None, None
    for line in open(raw, encoding="utf-8", errors="replace"):
        parts = line.rstrip("\n").split("\t", 2)
        if len(parts) == 3:
            step, text = parts[1], parts[2]
        else:  # continuation line of a multi-line log entry
            text = parts[-1]
        if step not in steps:
            continue
        echoed = "\x1b[36;1m" in text or "^[[36;1m" in text
        text = TS.sub("", ANSI.sub("", text))
        if echoed or NOISE.search(text) or (keep and not keep(step, text)):
            continue
        if step != last:
            out.append(f"▶ {step}")
            last = step
        out.append("  " + text)
    return out


def shot(out, title, lines):
    def fmt(x):
        cls = "s" if x.startswith("▶") else "e" if re.search(r"FAILED|Error|exit code [1-9]|\bfailed\b", x) else \
              "p" if re.search(r"PASSED|passed|SUCCESS|healthy|successfully|\"ok\"", x) else ""
        return f'<span class="{cls}">{html.escape(x)}</span>\n' if cls else html.escape(x) + "\n"
    body = "".join(fmt(x) for x in lines)
    w = min(1400, max(760, int(max(len(x) for x in lines) * 8.45) + 50))
    h = len(lines) * 19 + 80
    page = f"""<html><body style="margin:0;background:#1e1e1e"><div style="font:14px Menlo,monospace;color:#ddd">
<div style="background:#2d2d2d;padding:8px 12px;color:#aaa;text-align:center;position:relative">
<span style="position:absolute;left:12px;top:6px;color:#ff5f56">●</span><span style="position:absolute;left:30px;top:6px;color:#ffbd2e">●</span><span style="position:absolute;left:48px;top:6px;color:#27c93f">●</span>{html.escape(title)}</div>
<pre style="margin:0;padding:12px 18px;line-height:19px;white-space:pre">{body}</pre></div>
<style>.s{{color:#79c0ff;font-weight:bold}}.p{{color:#7ee787}}.e{{color:#ff7b72}}</style></body></html>"""
    p = os.path.join(os.environ.get("SP", "/tmp"), "_shot.html")
    open(p, "w").write(page)
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--hide-scrollbars", f"--window-size={w},{h}",
                    f"--screenshot={os.path.abspath(out)}", "file://" + p], capture_output=True)
    print(out, w, h)


def terminal(out, title, logs, maxlines=None):
    lines = []
    for f in logs:
        lines += open(f).read().rstrip("\n").split("\n")
    shot(out, title, lines[:maxlines] if maxlines else lines)


if __name__ == "__main__":
    L, S = "logs/", "screenshots/"
    pytest_lines = lambda s, t: s != "Run tests" or re.search(r"::|passed|failed|=====|TOTAL|app/|Error|assert", t)
    docker_lines = lambda s, t: s != "Build Docker image" or re.search(r"^#\d+ \[\d/6\]|naming to", t) and "sha256" not in t
    upload_lines = lambda s, t: "upload" not in s.lower() or re.search(r"[Aa]rtifact|uploaded|files", t)
    # GitHub Actions job logs: (log name, screenshot, title, steps to keep, line filter)
    jobs = [
        ("gh-ci-test", "09-ci-test-job", "CI · Test (Python 3.12)", ["Show runner info", "Run tests", "Upload test results"],
         lambda s, t: pytest_lines(s, t) and upload_lines(s, t)),
        ("gh-ci-security", "10-ci-security-job", "CI · Security Check", ["Check for sensitive files"], None),
        ("gh-ci-build", "11-ci-build-job", "CI · Build Application", ["Build application", "Show build output", "Upload build artifact"],
         upload_lines),
        ("gh-ci-docker", "12-ci-docker-job", "CI · Docker Build & Smoke Test", ["Build Docker image", "Run container", "Smoke test"],
         docker_lines),
        ("gh-ci-failed-test", "13-ci-failed-test-job", "CI · Test (Python 3.11) - FAILED run", ["Run tests"],
         lambda s, t: re.search(r"::|passed|failed|assert|Error|=====", t)),
        ("gh-cd-publish", "14-cd-publish-job", "CD · Publish Docker Image",
         ["Set image tag", "Log in to GitHub Container Registry", "Build and push image"],
         lambda s, t: s != "Build and push image" or re.search(r"^#\d+ (\[\d/6\]|pushing \S+ with|naming to)", t)
         and "sha256" not in t),
        ("gh-cd-deploy", "15-cd-deploy-job", "CD · Deploy to Production", ["Check deploy secret", "Log in to GitHub Container Registry",
         "Pull image", "Deploy container", "Verify deployment", "Upload deployment report"], upload_lines),
    ]
    for name, png, title, steps, keep in jobs:
        # .raw = `gh run view --job <id> --log > logs/<name>.raw` (not committed); .log = cleaned copy
        if os.path.exists(L + name + ".raw"):
            open(L + name + ".log", "w").write("\n".join(clean(L + name + ".raw", steps, keep)) + "\n")
        terminal(S + png + ".png", title, [L + name + ".log"], 70)

    # Local runs on my Mac
    local = [
        ("08-gh-deployments-secrets", "parth@mac: environments, secrets, deployments", ["07-gh-deployments"]),
        ("16-local-lint-test", "parth@mac: flake8 + pytest", ["01-lint", "02-test"]),
        ("17-local-build", "parth@mac: ./build.sh", ["03-build"]),
        ("18-local-docker", "parth@mac: docker build + run", ["04-docker-build", "05-docker-run"]),
        ("19-local-broken-test", "parth@mac: pytest after breaking add()", ["06-broken-test"]),
    ]
    for png, title, logs in local:
        terminal(S + png + ".png", title, [L + x + ".log" for x in logs])

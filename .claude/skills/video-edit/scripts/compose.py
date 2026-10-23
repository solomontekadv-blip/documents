#!/usr/bin/env python3
"""Final export: cut video + graphics layer + music 12 dB under the voice, -14 LUFS, H.264 1080x1920.

Music level: integrated loudness of the music is set exactly --duck dB below the voice.
Loudness: two-pass loudnorm to -14 LUFS, true peak -1 dBTP. The result is measured again
and printed, so the number is checked, not assumed.

Usage: python3 compose.py build/cut.mov build/gfx final.mp4 [--music music.mp3] [--duck 12] [--fps 30]
"""
import argparse
import json
import os
import re
import subprocess

TARGET_I, TARGET_TP, TARGET_LRA = -14.0, -1.0, 11.0


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=True)


def loudness(path, af_prefix=""):
    af = (af_prefix + "," if af_prefix else "") + f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}:print_format=json"
    p = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-vn", "-af", af, "-f", "null", "-"])
    return json.loads(re.findall(r"\{[^{}]*\}", p.stderr)[-1])


def probe(path):
    p = run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_name,width,height,r_frame_rate,codec_type:format=duration",
             "-of", "json", path])
    return json.loads(p.stdout)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cut")
    ap.add_argument("gfx_dir")
    ap.add_argument("out")
    ap.add_argument("--music")
    ap.add_argument("--duck", type=float, default=12.0, help="music this many dB under the voice")
    ap.add_argument("--fps", type=int, default=30)
    a = ap.parse_args()

    build = os.path.dirname(os.path.abspath(a.cut))
    dur = float(probe(a.cut)["format"]["duration"])
    mix = os.path.join(build, "mix.wav")

    # 1. audio mix
    voice_i = float(loudness(a.cut)["input_i"])
    if a.music:
        music_i = float(loudness(a.music)["input_i"])
        gain = (voice_i - a.duck) - music_i
        fade = min(1.5, dur / 4)
        fc = (f"[1:a]aresample=48000,volume={gain:.2f}dB,atrim=0:{dur:.3f},"
              f"afade=t=in:d=0.3,afade=t=out:st={dur - fade:.3f}:d={fade:.3f}[m];"
              f"[0:a]aresample=48000[v];[v][m]amix=inputs=2:duration=first:normalize=0[a]")
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", a.cut, "-stream_loop", "-1", "-i", a.music,
             "-filter_complex", fc, "-map", "[a]", "-c:a", "pcm_s24le", mix])
        print(f"voice {voice_i:.1f} LUFS, music {music_i:.1f} LUFS -> music gain {gain:+.1f} dB (sits {a.duck:.0f} dB under)")
    else:
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", a.cut, "-vn", "-ar", "48000", "-c:a", "pcm_s24le", mix])
        print(f"voice {voice_i:.1f} LUFS, no music")

    # 2. loudness pass 1 on the mix, pass 2 inside the final encode
    m = loudness(mix)
    ln = (f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}:measured_I={m['input_i']}:"
          f"measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:"
          f"offset={m['target_offset']}:linear=true,aresample=48000")

    # 3. video: graphics over the cut, H.264
    inputs = ["-i", a.cut, "-i", mix]
    if a.gfx_dir and os.path.isdir(a.gfx_dir) and os.listdir(a.gfx_dir):
        inputs += ["-framerate", str(a.fps), "-i", os.path.join(a.gfx_dir, "%05d.png")]
        vf = f"[0:v][2:v]overlay=0:0:eof_action=pass:format=auto,format=yuv420p[v]"
    else:
        print("no graphics frames found, exporting without the graphics layer")
        vf = "[0:v]format=yuv420p[v]"
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *inputs,
         "-filter_complex", f"{vf};[1:a]{ln}[a]", "-map", "[v]", "-map", "[a]",
         "-c:v", "libx264", "-profile:v", "high", "-preset", "slow", "-crf", "17", "-r", str(a.fps),
         "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
         "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-movflags", "+faststart", "-t", f"{dur:.3f}", a.out])

    # 4. verify, don't claim
    p = probe(a.out)
    v = next(s for s in p["streams"] if s["codec_type"] == "video")
    final = loudness(a.out)
    ok = (v["codec_name"] == "h264" and (v["width"], v["height"]) == (1080, 1920)
          and abs(float(final["input_i"]) - TARGET_I) <= 0.5 and float(final["input_tp"]) <= TARGET_TP + 0.2)
    print(f"{a.out}: {v['codec_name']} {v['width']}x{v['height']} {v['r_frame_rate']}fps, "
          f"{float(p['format']['duration']):.2f}s, {final['input_i']} LUFS, true peak {final['input_tp']} dBTP "
          f"-> {'PASS' if ok else 'FAIL'}")
    os.remove(mix)
    raise SystemExit(0 if ok else 2)


if __name__ == "__main__":
    main()

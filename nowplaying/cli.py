"""Консольный режим и точка входа."""
from __future__ import annotations

import argparse
import json
import sys
import time

from . import __version__
from .backends import BackendError, get_backend
from .models import format_time


def _line(t) -> str:
    state = "▶" if t.is_playing else "⏸"
    who = f"{t.artist} — {t.title}" if t.artist else t.title
    pos = format_time(t.current_position())
    dur = format_time(t.duration)
    return f"{state} [{t.source_name}] {who}  ({pos} / {dur})"


def run_cli(backend, interval: float, once: bool, as_json: bool) -> None:
    last_key = None
    try:
        while True:
            sessions = backend.get_sessions()
            if once:
                if as_json:
                    print(json.dumps([s.to_dict() for s in sessions], ensure_ascii=False, indent=2))
                elif not sessions:
                    print("Ничего не играет")
                else:
                    for s in sessions:
                        print(_line(s))
                return
            current = backend.get_current()
            key = (current.key, current.is_playing) if current else None
            if key != last_key:
                last_key = key
                if as_json:
                    print(json.dumps(current.to_dict() if current else None, ensure_ascii=False), flush=True)
                else:
                    print(_line(current) if current else "— ничего не играет —", flush=True)
            time.sleep(interval)
    except KeyboardInterrupt:
        pass
    finally:
        backend.close()


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        prog="nowplaying",
        description="Показывает, какая музыка сейчас играет на компьютере (браузер или приложение).",
    )
    p.add_argument("--cli", action="store_true", help="консольный режим: печатать смену треков")
    p.add_argument("--once", action="store_true", help="вывести текущее состояние и выйти")
    p.add_argument("--json", action="store_true", help="вывод в JSON")
    p.add_argument("--demo", action="store_true", help="демо-режим без реального плеера")
    p.add_argument("--interval", type=float, default=1.0, help="интервал опроса, сек (по умолчанию 1)")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = p.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    try:
        backend = get_backend(demo=args.demo)
    except BackendError as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 1

    if args.cli or args.once or args.json:
        run_cli(backend, args.interval, args.once, args.json)
    else:
        from .gui import run_gui
        run_gui(backend, args.interval)
    return 0

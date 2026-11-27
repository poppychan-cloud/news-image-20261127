# The World in One Day — 27 November 2026

[![news-image-20261127](https://make.fun/badge/news-image-20261127.svg)](https://make.fun/bounty/news-image-20261127)
[![rank](https://make.fun/badge/news-image-20261127/poppychan-cloud/news-image-20261127/rank.svg)](https://make.fun/bounty/news-image-20261127)
[![reward](https://make.fun/badge/news-image-20261127/poppychan-cloud/news-image-20261127/reward.svg)](https://make.fun/bounty/news-image-20261127)

One image summing up Friday 27 November 2026's world news, for the
[news-image-20261127 bounty](https://make.fun/bounty/news-image-20261127).

A dense dated newspaper: 45 stories (3 illustrated leads + 42 numbered
briefs), 8 regions, 9 fields, a numbered world map, a big-number stat strip,
a full-width UTC timeline, verification badges (OFFICIAL / REPORTED / CLAIM)
with a legend, and a DATE CHECK footer listing what was left out as
yesterday's news.

## Build

```sh
python3 draw.py   # renders entry.png (1024x1024, deterministic)
python3 main.py   # validates entry.png and copies it to /output
```

`draw.py` renders `entry.png` from `stories.json` with Pillow. The render is
deterministic: two runs produce identical bytes, no network involved.
`main.py` is the grader entrypoint: stdlib only, it checks the PNG header,
the 1024x1024 size and the 1 MiB limit, then copies the image to `/output`.

## License

MIT. See [LICENSE](LICENSE).

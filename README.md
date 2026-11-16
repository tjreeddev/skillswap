# SkillSwap

SkillSwap is a small web app that runs on your own computer. It helps
freelancers and small business owners find people to trade services with.

- Create a profile with your name, or choose an existing one.
- Add the services you offer and the services you want.
- See your matches: other people who offer something you want **and** want
  something you offer, along with the services that match.

Matching ignores capitalization and extra spaces, so "Logo Design" matches
"logo design". Part of a name does not count, so "logo" does not match
"logo design".

All profiles are saved to `data.json` in the folder you run the app from, so
they are still there after a restart.

## Requirements

- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/)

## Run the program

From the project folder:

```
uv run python -m skillswap
```

Then open http://127.0.0.1:5000 in your browser. Press `Ctrl+C` to stop.

## Run the tests

From the project folder:

```
uv run pytest
```

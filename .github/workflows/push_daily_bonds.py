name: push_bonds_daily

env:
  PYTHON_VERSION: "3.8" # set this to the Python version to use
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

on:
  schedule:
    - cron: '24 8 * * *' # 每天 UTC 时间 00:00 触发, 即上海时间9点

jobs:
  daily-push:
    runs-on: ubuntu-latest
    env:
      SERVERCHAN_API_KEY: ${{ secrets.SERVERCHAN_API_KEY }}

    permissions:
      issues: write
      contents: write

    steps:
      - uses: actions/checkout@v3
      - name: Set up Python version
        uses: actions/setup-python@v3
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          
      - name: Install dependencies
        run: pip install os requests re json


      - name: PUSH ARXIV DAILY
        run: python bonds.py
        
      - name: Commit files
        id: commit
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "github-actions"
          git add --all
          if [ -z "$(git status --porcelain)" ]; then
             echo "::set-output name=push::false"
          else
             git commit -m "chore: update confs" -a
             echo "::set-output name=push::true"
          fi
        shell: bash

      - name: Push changes
        if: steps.commit.outputs.push == 'true'
        uses: ad-m/github-push-action@master
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}

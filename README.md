dev

```
docker build -t words .
docker run -it --rm --name words -v $PWD:/app -p 8000:8000 -e DB_PATH=/app/words.db words bash run.sh
```

prod

```
fly launch
fly volumes create wordz_data --region ams --size 1 -a wordz
fly deploy
```

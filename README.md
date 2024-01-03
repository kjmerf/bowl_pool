# Bowl Pool

Given a CSV file with picks by bettors, you can use this repo to generate the paths to victory for each bettor.

For example, suppose your CSV files were in the ```sample_data``` directory. Then you could run:

```
python3 src/main.py sample_data/picks/picks.csv sample_data/multipliers/multipliers.csv sample_data/bowls/start.csv
```

The output is a file with every possible outcome including the winner for each scenario.

To run the unit tests, you can use:
```
python3 -m unittest discover
```

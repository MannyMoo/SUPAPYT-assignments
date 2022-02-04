# SUPAPYT 2022 assignment

The file [here](PerCapitaC02Emissions.csv) contains data on historical, per-capita C02 emissions for countries around the world, from [The World Bank](https://data.worldbank.org/indicator/EN.ATM.CO2E.PC?view=chart). The assignment is to analyse these data and extract some interesting information. Only functionality from the [Standard Library](https://docs.python.org/3/tutorial/stdlib.html) is allowed as I want to be able to run your code with a basic python installation without installing any extra packages (so no `numpy`, `pandas`, etc - the full list of allowed modules is [here](https://docs.python.org/3/library/index.html)).

Download the [data file](PerCapitaC02Emissions.csv), which is a simple spreadsheet in plain text. The names of the columns are given in the first line. They are "Country Name", "Region", "IncomeGroup", and years from 1960-2018. The rows contain the data for each country - name, region, & income group, followed by their per-capita emissions in each year. Some countries are missing data for some years. When analysing such countries, you should skip over those years.

Write a script/module/package in python to do the following:

1) Find the countries with the lowest and highest emissions in 1960, and similarly in 2018 (ignoring countries with no data for the given year). Print the names of the countries and their emissions for each year.

2) Find the and print mean and standard deviation of the emissions across all countries in 1960 & 2018 (ignoring countries that have no data for the given year).

3) Find the countries with the lowest and highest total emissions summed over all years (ignoring missing years for each country). Print their names and total emissions.

4) Sum the total emissions for all countries in each region across all years. Print a list of the regions and their total emissions, ordered by their emissions. Do the same grouping the countries by income group.

5) Similarly to problem 4, group the countries by region, then, for each decade in the range 1960s-2010s, calculate the total emissions of each region in that decade, then print the regions and their total emissions sorted by emissions. A decade is defined as, eg, 1960-1969 inclusive (or 2010-2018 for 2010s as there's no data for 2019). Do the same grouping the countries by income group.

Again, only [Standard Library](https://docs.python.org/3/library/index.html) functionality is allowed. The [`csv`](https://docs.python.org/3/library/csv.html) module can help with reading the data file.

Upload your solution scripts here. A Jupyter notebook is also accepted. I will execute the code with the original data file in the same directory.

Solutions will be graded not just on obtaining the correct answers but also on the readability of the code and its output, how well structured the code is, and how well you make use of python functionality. Consider that you might want to rerun your code when additional years or countries are added to the data file and remember the [coding tips](https://mannymoo.github.io/IntroductionToPython/SUPAPYT-IntroductionToPython.html#A-Few-Tips) from the lectures.

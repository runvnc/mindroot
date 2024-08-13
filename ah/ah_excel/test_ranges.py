import ranges

filename = "/xfiles/ah/ah/ah_excel/example.xlsx"
range_name = "ExpensesBox"

result = ranges.read_ranges(filename, [range_name])
print(f"Result for {range_name}:")
print(result)

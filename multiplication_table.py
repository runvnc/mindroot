def print_multiplication_table(size):
    header = '    ' + '   '.join(f'{i:2}' for i in range(1, size + 1))
    print(header)
    print('   ' + '-' * (len(header) - 3))
    for i in range(1, size + 1):
        row = f'{i:2} |' + ' '.join(f'{i * j:3}' for j in range(1, size + 1))
        print(row)

if __name__ == '__main__':
    print_multiplication_table(10)

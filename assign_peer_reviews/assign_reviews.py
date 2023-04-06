from z3 import *

n_row = 10  # size of matrices
n_col = 32

#columns are representing the different groups to be assigned to, i.e., 32 groups in total
#rows are representing the different presentation groups to be assigned with groups for reviewing, i.e., 10 presentation groups in total are presenting their work
#the sum of each row should be 2, where 2 means that each presentation group is assigned with 2 groups for reviewing

# thanks github.com/rohithpudari for formalizating the matrix construction 
# Declare a matrix M1 as n_row × n_col matrices of integer variables
M1 = [[Int(f'M1_{i}_{j}') for j in range(n_col)] for i in range(n_row)]


s = z3.Solver()

# Ensure all entries in M1 and M2 are non-negative
for i in range(n_row):
    for j in range(n_col):
        s.add(M1[i][j] >= 0)
        s.add(M1[i][j] <= 1)

# Ensure that the rows of M1 sum to 2
for i in range(n_row):
    row_sum1 = Sum([M1[i][j] for j in range(n_col)])
    #if the total group number is not 33, then the sum of each row should be 6 or 7
    s.add(Or(row_sum1 == 6,row_sum1 == 7))
    #if the total group number is 33, then the sum of each row should be 6
    # s.add(row_sum1 == 6)


# Ensure that the columns of M1 sum to 6
for j in range(n_col):
    col_sum1 = Sum([M1[i][j] for i in range(n_row)])
    s.add(col_sum1 == 2)

# ensure that the diagonal is not 1
for i in range(n_row):
    s.add(M1[i][i] == 0)

# ensure the neighboring cells are 0
for i in range(n_row):
    for j in range(n_col):
        if i-j == 1 or i-j == -1 or j-i == 1 or j-i == -1:
            s.add(M1[i][j] == 0)


# Find the first solution that satisfies the constraints
if s.check() == sat:
    m1 = s.model()
    print("the matrix M1 the satisfy the constraints:")
    for i in range(n_row):
        for j in range(n_col):
            print(m1[M1[i][j]], end=' ')
        print()
    print()

else:
    print("No solutions found")

# map the matrix to a list of lists
list_M1 = [[m1[M1[i][j]] for j in range(n_col)] for i in range(n_row)]

# 32 groups on the presentation day, where the preseneting groups are the first 10 groups in the list
groups=['Group1','Group2','Group3','Group4','Group5','Group6','Group7','Group8','Group9','Group10','Group11','Group12',
        'Group13','Group14','Group15','Group16','Group17','Group18','Group19','Group20','Group21','Group22','Group23','Group24','Group25','Group26','Group27','Group28','Group29','Group30','Group31','Group32']

assignments = {}
# map the matrix to the groups list, with the index of the group in the list being the index of the column in the matrix, and the index of the row being the index of the first 10 elements in the group
for i in range(len(list_M1)):
    assignments[groups[i]] = [groups[j] for j in range(len(list_M1[i])) if list_M1[i][j] == 1]

#store the assignments in a json file
import json
with open('assign_peer_reviews/peer_review_assignment.json', 'w') as fp:
    json.dump(assignments, fp)

from scipy.special import comb

def hypergeom_pmf(N, A, n, x):
    
    '''
    Probability Mass Function for Hypergeometric Distribution
    :param N: population size
    :param A: total number of desired items in N
    :param n: number of draws made from N
    :param x: number of desired items in our draw of n items
    :returns: PMF computed at x
    '''
    Achoosex = comb(A,x)
    NAchoosenx = comb(N-A, n-x)
    Nchoosen = comb(N,n)
    
    return (Achoosex)*NAchoosenx/Nchoosen

def calculate_multiple_estadistics(N, A, n, x):
    '''
    Calculates the PMF and the CDF of the hypergeometric distribution
    :param N: population size
    :param A: total number of desired items in N
    :param n: number of draws made from N
    :param x: number of desired items in our draw of n items
    :returns: PMF and CDF of the hypergeometric distribution
    '''
    
    exactamente = hypergeom_pmf(N, A, n, x)
    
    menorIgualA = 0
    for i in range(x+1):
        menorIgualA += hypergeom_pmf(N, A, n, i)
    
    menorA = 0
    for i in range(x):
        menorA += hypergeom_pmf(N, A, n, i)
    mayorIgualA = 0
    for i in range(x,n+1):
        mayorIgualA += hypergeom_pmf(N, A, n, i)
    mayorA = 0
    for i in range(x+1, n+1):
        mayorA += hypergeom_pmf(N, A, n, i)
    return exactamente, menorA, menorIgualA, mayorA, mayorIgualA

def PrintEstadisticas(N, A, n, x):
    '''
    Prints the PMF and the CDF of the hypergeometric distribution
    :param N: population size
    :param A: total number of desired items in N
    :param n: number of draws made from N
    :param x: number of desired items in our draw of n items
    :returns: PMF and CDF of the hypergeometric distribution
    '''
    exactamente, menorA, menorIgualA, mayorA, mayorIgualA = calculate_multiple_estadistics(N, A, n, x)
    return f'''Exactamente:    {format(exactamente*100, ".2f"):0>5}%
Mayor Igual A:   {format(mayorIgualA*100, ".2f"):0>5}%'''

#     return f'''Exactamente:    {format(exactamente*100, ".2f"):0>5}%
# Menor A:        {format(menorA*100, ".2f"):0>5}%
# Menor Igual A   {format(menorIgualA*100, ".2f"):0>5}%
# Mayor A:        {format(mayorA*100, ".2f"):0>5}%
# Mayor Igual A   {format(mayorIgualA*100, ".2f"):0>5}%'''

if __name__ == '__main__':
    print(PrintEstadisticas(52,13,5,3))

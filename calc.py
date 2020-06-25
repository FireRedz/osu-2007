def accCalc(count300: int, count100: int, count50: int,countmiss: int):
        ### MATH SHIT
        acc =  ((count300 * 300 + count100 * 100 + count50 * 50 + countmiss * 0)/((count300 + count100 + count50 + countmiss) * 300) * 100) 

        return acc



print(accCalc(6, 0,2,6))
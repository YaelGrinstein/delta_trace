import numpy as np
count_me = 0

class DeltaCorrection():

    def __init__(self):
        self.header = None

    def fit(self, processed_data, raw_data):

        #print("measure_1", processed_data)
        #print("measure_2", raw_data)

        measure_1 = self.row2matrix(np.array_str(processed_data))
        measure_2 = self.row2matrix(np.array_str(raw_data))
        fixed_mat = self.fix_delta(measure_1, measure_2)
        fixed_row_data = self.matrix2rowdata(fixed_mat)
        print("fixed_row_data", fixed_row_data)

        return fixed_row_data

    def matrix2rowdata(self, fixed_mat):

        xy_corr = np.nonzero(fixed_mat)
        x_list = xy_corr[0].tolist()
        y_list = xy_corr[1].tolist()
        data_temp = []
        for x, y in zip(x_list, y_list):
            if self.A_R_matrix[x, y] == 1:
                data_temp.append('A' + str([x, y, fixed_mat[x][y]]))
            elif self.A_R_matrix[x, y] == 2:
                data_temp.append('R' + str([x, y, fixed_mat[x][y]]))
            else:
                data_temp.append(str([x, y, fixed_mat[x][y]]))
        temp = (','.join([str(n) for n in data_temp])).replace('[', '')
        temp = temp.replace(']', '')
        boardID = self.header.split(',')[1]
        packet = self.header + temp
        data = {'boardId': boardID, 'packet': packet}

        #print("the update row data is: \n", data)
        return data


    def row2matrix(self, raw_data):
        matrix = (np.zeros((120, 45))).astype(int)
        self.A_R_matrix = np.zeros_like(matrix)
        #data = raw_data['packet']
        data = raw_data
        self.header = data.split("!,")[0] + "!,"
        packet = (data.split("!,")[1]).split(",")
        for i, str in enumerate(packet):
            if str.find('A') != -1:
                x = int(str.replace('A', ''))
                y = int(packet[i + 1])
                self.A_R_matrix[x, y] = 1
            if str.find('R') != -1:
                x = int(str.replace('R', ''))
                y = int(packet[i + 1])
                self.A_R_matrix[x, y] = 2

        coor_and_val = (data.split("!,")[1]).replace('A', '')

        coor_and_val = coor_and_val.replace('R', '')
        coor_and_val = coor_and_val.split(",")
        if  '' in coor_and_val:
            coor_and_val.pop()
        data = [int(x) for x in coor_and_val]
        i = 0
        while data:
            matrix[data[i], data[i + 1]] = data[i + 2]
            i = i + 3
            if i == (len(data) - 3):
                break
        return matrix

    def fix_delta(self, measure_1, measure_2):

        # get the active areas in both measurements
        temp_1 = np.zeros_like(measure_1)
        temp_1[np.nonzero(measure_1 != 0)] = 1
        temp_2 = np.zeros_like(measure_2)
        temp_2[np.nonzero(measure_2 != 0)] = 1

        # refer the case where a point in measure_2 decrease to zero - takes as zero
        measure_1 = temp_2 * measure_1

        # the matrix contain the same pixels from the previous measurement after decay
        diff_mat = temp_1 * measure_2

        # refer the case where measure _2 get a higher value compare to measure _1 - takes the max value
        ref_mat = np.maximum(measure_1, diff_mat)

        # takes only the new points
        temp_ref = np.zeros_like(ref_mat)
        temp_ref[np.nonzero(ref_mat != 0)] = 1
        new_points_mat = measure_2.copy()
        new_points_mat[temp_ref == 1] = 0

        # calculates the delta values
        delta_and_newPoints = np.abs(ref_mat - measure_2)
        delta_mat = delta_and_newPoints - new_points_mat
        # summarizes all deltas per column and add it to the active values in the next measurement
        # creates a reference matrix for the next measurement
        num_of_deltas_per_col = np.count_nonzero(delta_mat, axis=0)
        total_deltas_per_col = np.sum(delta_mat, axis=0)
        avg_delta_per_col = (total_deltas_per_col / num_of_deltas_per_col)
        avg_delta_per_col[np.isnan(avg_delta_per_col)] = 0
        new_points = np.nonzero(new_points_mat)
        for row, col in zip(new_points[0], new_points[1]):
            res = int(avg_delta_per_col[col]) + measure_2[row, col]
            if res > 4096:
                res = 4096
            ref_mat[row, col] = res
        return ref_mat











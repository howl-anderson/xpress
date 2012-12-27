import os
def get_file_list(dir):
    result=[]
    yid = os.walk(dir)
    for rootDir,pathList,fileList in yid:
        for file in fileList:
            result.append(os.path.join(rootDir,file))
    return result
file_list = get_file_list(".")
def get_ctime_list(file_list):
    result={}
    for file in file_list:
        file_stat = os.stat(file)
        result[file]=file_stat.st_ctime
    return result
file_ctime = get_ctime_list(file_list)
print file_ctime
d=file_ctime
ctime_sort = sorted(d, key=d.__getitem__, reverse=True)
print ctime_sort

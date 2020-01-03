'''
@Author: xuchenming
@Date: 2020-01-03 06:04:24
@LastEditTime : 2020-01-03 06:19:01
@LastEditors  : Please set LastEditors
@Description: In User Settings Edit
@FilePath: /ecust_annotation/api/consistency.py
'''
class Consistency:
    def __init__(self,annos):
        self.annos = annos
    
    @staticmethod
    def dicEntitytoTuple(entity):#输入实体的字典表示，输出实体的元组表示
        return (entity["start_offset"],entity["end_offset"],entity["entity_template"])
    
    def getEntitySet(self,doc):#输入一条文本dic，返回两个标注者的标注结果set的dic
        anno1 = set(map(self.dicEntitytoTuple,doc["annotation_one"]))
        anno2 = set(map(self.dicEntitytoTuple,doc["annotation_two"]))
        return {doc["annotation_one"][0]["user"]:anno1,doc["annotation_two"][0]["user"]:anno2}
    
    @staticmethod
    def compF1Score(pred,truth):#计算F1值，输入是两个set
        TP = len(pred&truth)#预测为正例且正确的数目
        FP = len(pred-truth)#预测为正例但错误的数目
        FN = len(truth-pred)#预测为负例但错误的数目
        precision = TP/(TP+FP)
        recall = TP/(TP+FN)
        return 2*precision*recall/(precision+recall)
    
    def getSimScore(self,func=None):#返回一致性得分列表[{doc_id:sim_score}]
        if func == None:
            func = self.compF1Score
        sim_score_list = []
        for doc in self.annos:
            anno = list(self.getEntitySet(doc).values())
            anno1 = anno[0]
            anno2 = anno[1]
            #计算1条文本doc的两个标注结果的一致性得分。
            sim_score = 0.5*(func(anno1,anno2)+func(anno2,anno1))
            sim_score_list.append({doc["doc_id"]:sim_score})
        return sim_score_list
    
    def refusedDocList(self,accept=0.5,func=None):#返回拒绝文本id列表。accept是接受标注结果的一致性得分，当一致性得分大于等于accept时接受
        doc_list = []
        sim_score_list = self.getSimScore(func)
        for sim_score in sim_score_list:
            for k,v in sim_score.items():
                if v<accept:
                    doc_list.append(k)
        return doc_list
    
    def getDifference(self,doc=None):#输入doc的dic,输出两个标注结果的差集
        if doc == None:
            doc = self.annos[0]
        diff = {"different_set":{"annotation_one":[],"annotation_two":[]}}
        anno = self.getEntitySet(doc)
        user1,user2 = tuple(anno.keys())
        diff1 = anno[user1]-anno[user2]
        diff2 = anno[user2]-anno[user1]
        for i in diff1:
            diff["different_set"]["annotation_one"].append({"start_offset":i[0],"end_offset":i[1],"entity_template":i[2],"user":user1})
        for i in diff2:
            diff["different_set"]["annotation_two"].append({"start_offset":i[0],"end_offset":i[1],"entity_template":i[2],"user":user2})
        return diff
    
    def getIntersection(self,doc=None):#输入doc的dic,输出两个标注结果的交集
        if doc == None:
            doc = self.annos[0]
        inter = {"intersection":[]}
        anno = self.getEntitySet(doc)
        user1,user2 = tuple(anno.keys())
        inter_temp = anno[user1]&anno[user2]
        for i in inter_temp:
            inter["intersection"].append({"start_offset":i[0],"end_offset":i[1],"entity_template":i[2]})
        return inter
    
    def getDiffInter(self,doc=None):#输入doc的dic,输出两个标注结果的并集和交集
        if doc == None:
            doc = self.annos[0]
        diff = self.getDifference(doc)
        inter = self.getIntersection(doc)
        diff.update(inter)
        return diff
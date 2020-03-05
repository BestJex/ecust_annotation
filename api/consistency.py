'''
@Author: xuchenming
@Date: 2020-01-03 06:04:24
@LastEditTime: 2020-03-04 21:23:57
@LastEditors: Please set LastEditors
@Description: In User Settings Edit
@FilePath: /ecust_annotation/api/consistency.py
'''
class Consistency:
    def __init__(self,annos):
        self.annos = annos
#     "start_entity": 1,
#                 "end_entity": 2,
#                 "relation_template": 5
    @staticmethod
    def dicEntitytoTuple(entity):#输入实体的字典表示，输出实体的元组表示
        return (entity["start_offset"],entity["end_offset"],entity["entity_template"],entity["content"])
    
    def getEntitySet(self,doc=None):#输入一条文本dic，返回两个标注者的实体标注结果set的dic
        if doc == None:
            doc = self.annos[0]
        anno1 = set(map(self.dicEntitytoTuple,doc["annotation_one"]["entity"]))
        anno2 = set(map(self.dicEntitytoTuple,doc["annotation_two"]["entity"]))
        return {"annotation_one":anno1,"annotation_two":anno2}
    
    def getEntityUnion(self,doc=None):#输入doc列表，输出doc中标注的实体列表
        if doc == None:
            doc = self.annos
            
        anno1 = set(map(self.dicEntitytoTuple,doc["annotation_one"]["entity"]))
        anno2 = set(map(self.dicEntitytoTuple,doc["annotation_two"]["entity"]))
        return list(anno1|anno2)
    
    def getOneRelationSet(self,doc,entity_hash,annotation_x):#得到标注者1或2的关系标注集合
            res = set([])
            if "relation" not in doc[annotation_x].keys():
                return res
            else:
                for i in doc[annotation_x]["relation"]:
                    flag1 = 0
                    flag2 = 0

                    for j in doc[annotation_x]["entity"]:#找到头实体尾实体id对应的原实体
                        if flag1 == 0 and i["start_entity"]==j["id"]:
                            flag1 = 1
                            start_entity = self.dicEntitytoTuple(j)
                        if flag2 == 0 and i["end_entity"]==j["id"]:
                            flag2 = 1
                            end_entity = self.dicEntitytoTuple(j)
                        if flag1 == 1 and flag2 == 1:
                            break

                    res.add((entity_hash.index(start_entity),entity_hash.index(end_entity),i["relation_entity_template"]))
                return res
    
    def getRelationSet(self,doc,entity_hash=None):#输入一条文本dic，返回两个标注者的关系标注结果set的dic
        if entity_hash == None:
            entity_hash = self.getEntityUnion(doc)
        return {"annotation_one":self.getOneRelationSet(doc,entity_hash,"annotation_one"),"annotation_two":self.getOneRelationSet(doc,entity_hash,"annotation_two")},entity_hash
            
    @staticmethod
    def compF1Score(pred,truth):#计算F1值，输入是两个set
        TP = len(pred&truth)#预测为正例且正确的数目
        FP = len(pred-truth)#预测为正例但错误的数目
        FN = len(truth-pred)#预测为负例但错误的数目
        if TP == 0:
            return 0
        precision = TP/(TP+FP)
        recall = TP/(TP+FN)
        return 2*precision*recall/(precision+recall)
    
    def getSimScore(self,func=None):#返回一致性得分列表[{doc_id:sim_score}]
        sim_score_list = []
        for doc in self.annos:
            if doc["annotation_type"] == "NER":
                sim_score = NER_Consistency.getSimScore(self,doc,func)
                sim_score_list.append({doc["doc_id"]:("NER",sim_score)})
                
            elif doc["annotation_type"] == "RE":
                sim_score = RE_Consistency.getSimScore(self,doc,func)
                sim_score_list.append({doc["doc_id"]:("RE",sim_score)})

            elif doc["annotation_type"] == "EVENT":
                print("ERROR: Todo")
                pass

            elif doc["annotation_type"] == "CLASSIFICATION":
                print("ERROR: Todo")
                pass
            
        return sim_score_list
    
    def refusedDocList(self,sim_score_list,accept=0.5):#返回拒绝文本id列表。accept是接受标注结果的一致性得分，当一致性得分大于等于accept时接受
        doc_list = []
        for sim_score in sim_score_list:
            for k,v in sim_score.items():
                if v[1]<accept:
                    doc_list.append(k)
                    
        return doc_list
    
    def getDifference(self,doc=None,entity_hash=None):#针对单文档的两个标注结果的两个差集。如果输入的是一个文档列表，则默认列表中第一个文档
        if doc == None:
            doc = self.annos[0]
            
        if doc["annotation_type"] == "NER":
            return NER_Consistency.getDifference(self,doc)
        
        elif doc["annotation_type"] == "RE":
            if entity_hash==None:
                entity_hash = self.getEntityUnion(doc)
            return RE_Consistency.getDifference(self,doc,entity_hash)
        
        elif doc["annotation_type"] == "EVENT":
            print("ERROR: Todo")
            pass
        
        elif doc["annotation_type"] == "CLASSIFICATION":
            print("ERROR: Todo")
            pass
        
    def getIntersection(self,doc=None,entity_hash=None):#针对单文档的两个标注结果的交集。如果输入的是一个文档列表，则默认列表中第一个文档
        if doc == None:
            doc = self.annos[0]
            
        if doc["annotation_type"] == "NER":
            return NER_Consistency.getIntersection(self,doc)
        
        elif doc["annotation_type"] == "RE":
            if entity_hash==None:
                entity_hash = self.getEntityUnion(doc)
            return RE_Consistency.getIntersection(self,doc,entity_hash)
        
        elif doc["annotation_type"] == "EVENT":
            print("ERROR: Todo")
            pass
        
        elif doc["annotation_type"] == "CLASSIFICATION":
            print("ERROR: Todo")
            pass
        
        
    def getDiffInter(self,doc=None,entity_hash=None):#针对单文档的两个标注结果的交集和两个差集（三个集合相加，则为两个标注结果的并集；相比直接取并集更慢，但信息更丰富）。如果输入的是一个文档列表，则默认列表中第一个文档
        if doc == None:
            doc = self.annos[0]

        if doc["annotation_type"] == "NER":
            return NER_Consistency.getDiffInter(self,doc)
        
        elif doc["annotation_type"] == "RE":
            if entity_hash==None:
                entity_hash = self.getEntityUnion(doc)
            return RE_Consistency.getDiffInter(self,doc,entity_hash)
        
        elif doc["annotation_type"] == "EVENT":
            print("ERROR: Todo")
            pass
        
        elif doc["annotation_type"] == "CLASSIFICATION":
            print("ERROR: Todo")
            pass
        
    def getUnion(self):#针对单文档的两个标注结果的交集和两个差集（三个集合相加，则为两个标注结果的并集；相比直接取并集更慢，但信息更丰富）。如果输入的是一个文档列表，则默认列表中第一个文档
        annos = self.annos
        union = []
        for doc in annos:
        
            if doc["annotation_type"] == "NER":
                union.append(NER_Consistency.getUnion(self,doc))

            elif doc["annotation_type"] == "RE":
                union.append(RE_Consistency.getUnion(self,doc))

            elif doc["annotation_type"] == "EVENT":
                print("ERROR: Todo")
                pass

            elif doc["annotation_type"] == "CLASSIFICATION":
                print("ERROR: Todo")
                pass
        return union

class NER_Consistency(Consistency):
    def getSimScore(self,doc,func=None):#getSimScore方法在NER任务中的实现（实体级别）。见Consistency.getSimScore
        if func == None:
            func = self.compF1Score
        
        anno = list(self.getEntitySet(doc).values())
        anno1 = anno[0]
        anno2 = anno[1]
        #计算1条文本doc的两个标注结果的一致性得分。
        sim_score = 0.5*(func(anno1,anno2)+func(anno2,anno1))
        return sim_score
    
    def getDifference(self,doc=None):#getDifference方法在NER任务中的实现（实体级别）。见Consistency.getDifference
        if doc == None:
            doc = self.annos[0]
        diff = {"different_set":{"annotation_one":[],"annotation_two":[]}}
        anno = self.getEntitySet(doc)
        #         user1,user2 = tuple(anno.keys())
        diff1 = anno["annotation_one"]-anno["annotation_two"]
        diff2 = anno["annotation_two"]-anno["annotation_one"]
        for i in diff1:
            diff["different_set"]["annotation_one"].append({"start_offset":i[0],"end_offset":i[1],"entity_template":i[2],"content":i[3]})
        for i in diff2:
            diff["different_set"]["annotation_two"].append({"start_offset":i[0],"end_offset":i[1],"entity_template":i[2],"content":i[3]})
        return diff
    
    def getIntersection(self,doc=None):#getIntersection方法在NER任务中的实现（实体级别）。见Consistency.getIntersection
        if doc == None:
            doc = self.annos[0]
        inter = {"intersection":[]}
        anno = self.getEntitySet(doc)
        #         user1,user2 = tuple(anno.keys())
        inter_temp = anno["annotation_one"]&anno["annotation_two"]
        for i in inter_temp:
            inter["intersection"].append({"start_offset":i[0],"end_offset":i[1],"entity_template":i[2],"content":i[3]})
        return inter
    
    def getDiffInter(self,doc=None):#getDiffInter方法在NER任务中的实现（实体级别）。见Consistency.getIntersection
        if doc == None:
            doc = self.annos[0]
        diff = self.getDifference(doc)
        inter = self.getIntersection(doc)
        diff.update(inter)
        return diff
    
    def getUnion(self,doc):#有别于Consistency.getEntityUnion，这是未元组化的集合，实际应用中无需求

        entity = []
        diff = self.getDifference(doc)
        inter = self.getIntersection(doc)
#         print(inter)
        ori_entity = inter["intersection"]+diff["different_set"]["annotation_one"]+diff["different_set"]["annotation_two"]
        return {"doc_id":doc["doc_id"],"entity":ori_entity}
        
class RE_Consistency(NER_Consistency):
    def getSimScore(self,doc,func=None):
        if func == None:
            func = self.compF1Score
        relation_set,entity_hash = self.getRelationSet(doc)
        anno = list(relation_set.values())
        anno1 = anno[0]
        anno2 = anno[1]
        #计算1条文本doc的两个标注结果的一致性得分。
        sim_score = 0.5*(func(anno1,anno2)+func(anno2,anno1))
        return sim_score
    
    def getDifference(self,doc=None,entity_hash=None):#getDifference方法在RE任务中的实现（关系级别）。见Consistency.getDifference
        if doc == None:
            doc = self.annos[0]
        if entity_hash == None:
            entity_hash = self.getEntityUnion(doc)
        diff = {"different_set":{"annotation_one":[],"annotation_two":[]}}
        anno,_ = self.getRelationSet(doc,entity_hash)
#         user1,user2 = tuple(anno.keys())
        diff1 = anno["annotation_one"]-anno["annotation_two"]
        diff2 = anno["annotation_two"]-anno["annotation_one"]
        for i in diff1:
            diff["different_set"]["annotation_one"].append({"start_entity":i[0],"end_entity":i[1],"relation_entity_template":i[2]})
        for i in diff2:
            diff["different_set"]["annotation_two"].append({"start_entity":i[0],"end_entity":i[1],"relation_entity_template":i[2]})
        
        return diff,entity_hash
    
    def getIntersection(self,doc=None,entity_hash=None):#getIntersection方法在RE任务中的实现（关系级别）。见Consistency.getIntersection
        if doc == None:
            doc = self.annos[0]
        if entity_hash == None:
            entity_hash = self.getEntityUnion(doc)
        inter = {"intersection":[]}
        anno,_ = self.getRelationSet(doc,entity_hash)
#         user1,user2 = tuple(anno.keys())
        inter_temp = anno["annotation_one"]&anno["annotation_two"]
        for i in inter_temp:
            inter["intersection"].append({"start_entity":i[0],"end_entity":i[1],"relation_entity_template":i[2]})
        return inter,entity_hash
    
    def getDiffInter(self,doc=None,entity_hash=None):#getDiffInter方法在RE任务中的实现（关系级别）。见Consistency.getIntersection
        if doc == None:
            doc = self.annos[0]
        if entity_hash == None:
            entity_hash = self.getEntityUnion(doc)
        diff,_ = self.getDifference(doc,entity_hash)
        inter,_ = self.getIntersection(doc,entity_hash)
        diff.update(inter)
        return diff,entity_hash
    
    def getUnion(self,doc):
        
        def entityHashtoEntity(content,entity_hash):
            entity = []
            for i in entity_hash:
                entity.append({"start_offset":i[0],"end_offset":i[1],"entity_template":i[2],"content":i[3]})
            return entity
  
        entity_hash = self.getEntityUnion(doc)
        diff,_ = self.getDifference(doc,entity_hash)
        inter,_ = self.getIntersection(doc,entity_hash)
        relation = inter["intersection"]+diff["different_set"]["annotation_one"]+diff["different_set"]["annotation_two"]
        return {"doc_id":doc["doc_id"],"entity":entityHashtoEntity(doc["content"],entity_hash),"relation":relation}
             
    
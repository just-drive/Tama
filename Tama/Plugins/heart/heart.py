from task import task
import json
import networkx as nx
import matplotlib.pyplot as plt
from yapsy.IPlugin import IPlugin

class Heart(IPlugin):
    def __init__(self):
        super().__init__()
        self.tama_path = None
        self.emotion_graph = None
        return

    def work_task(self, task):
        if task.is_done():
            #This bit means a task that is done has been received.
            #So call the function in the task with the result to work with it.
            #Then set the task for removal
            getattr(self, task.get_func())(task.get_result())
            task.set_result('REMOVE')
        else:
            #This bit means a task needs to be done, and this method
            #might need to repackage the task so it gets returned.
            task.set_result(getattr(self, task.get_func())(task.get_args()))
            task.set_done(True)
            if task.get_requires_feedback():
                sender = task.get_sender()
                task.set_sender(task.get_plugin())
                task.set_plugin(sender)
            else:
                task.set_result('REMOVE')
        return task

    def set_tama_path(self, path):
        self.tama_path = path
        emotion_graph_path = path + '/Plugins/Heart/emotion_graph.gml'
        try:
            #this statement errors if the file doesn't exist yet, so I can create the base graph 
            #in the except clause and save it to file to handle this
            self.emotion_graph = nx.readwrite.read_gml(emotion_graph_path, 'label')
        except:
            self.emotion_graph = nx.DiGraph()
            
            #Add surprised emotions
            self.emotion_graph.add_edge('surprised', 'excited')
            self.emotion_graph.add_edge('surprised', 'amazed')
            self.emotion_graph.add_edge('surprised', 'confused')
            self.emotion_graph.add_edge('surprised', 'startled')
            self.emotion_graph.add_edge('excited', 'eager')
            self.emotion_graph.add_edge('excited', 'energetic')
            self.emotion_graph.add_edge('amazed', 'astonished')
            self.emotion_graph.add_edge('amazed', 'awe')
            self.emotion_graph.add_edge('confused', 'disillusioned')
            self.emotion_graph.add_edge('confused', 'perplexed')
            self.emotion_graph.add_edge('startled', 'shocked')
            self.emotion_graph.add_edge('startled', 'dismayed')

            #Add bad emotions
            self.emotion_graph.add_edge('bad', 'tired')
            self.emotion_graph.add_edge('bad', 'stressed')
            self.emotion_graph.add_edge('bad', 'busy')
            self.emotion_graph.add_edge('bad', 'bored')
            self.emotion_graph.add_edge('tired', 'sleepy')
            self.emotion_graph.add_edge('tired', 'unfocussed')
            self.emotion_graph.add_edge('stressed', 'overwhelmed')
            self.emotion_graph.add_edge('stressed', 'out of control')
            self.emotion_graph.add_edge('busy', 'pressured')
            self.emotion_graph.add_edge('busy', 'rushed')
            self.emotion_graph.add_edge('bored', 'indifferent')
            self.emotion_graph.add_edge('bored', 'apathetic')

            #Add fearful emotions
            self.emotion_graph.add_edge('fearful', 'scared')
            self.emotion_graph.add_edge('fearful', 'anxious')
            self.emotion_graph.add_edge('fearful', 'insecure')
            self.emotion_graph.add_edge('fearful', 'weak')
            self.emotion_graph.add_edge('fearful', 'rejected')
            self.emotion_graph.add_edge('fearful', 'threatened')
            self.emotion_graph.add_edge('scared', 'helpless')
            self.emotion_graph.add_edge('scared', 'frightened')
            self.emotion_graph.add_edge('anxious', 'overwhelmed')
            self.emotion_graph.add_edge('anxious', 'worried')
            self.emotion_graph.add_edge('insecure', 'inadequate')
            self.emotion_graph.add_edge('insecure', 'inferior')
            self.emotion_graph.add_edge('weak', 'worthless')
            self.emotion_graph.add_edge('weak', 'insignificant')
            self.emotion_graph.add_edge('rejected', 'excluded')
            self.emotion_graph.add_edge('rejected', 'persecuted')
            self.emotion_graph.add_edge('threatened', 'nervous')
            self.emotion_graph.add_edge('threatened', 'exposed')
            
            #Add angry emotions
            self.emotion_graph.add_edge('angry', 'let down')
            self.emotion_graph.add_edge('angry', 'humiliated')
            self.emotion_graph.add_edge('angry', 'bitter')
            self.emotion_graph.add_edge('angry', 'mad')
            self.emotion_graph.add_edge('angry', 'aggressive')
            self.emotion_graph.add_edge('angry', 'frustrated')
            self.emotion_graph.add_edge('angry', 'distant')
            self.emotion_graph.add_edge('angry', 'critical')
            self.emotion_graph.add_edge('let down', 'betrayed')
            self.emotion_graph.add_edge('let down', 'resentful')
            self.emotion_graph.add_edge('humiliated', 'disrespected')
            self.emotion_graph.add_edge('humiliated', 'ridiculed')
            self.emotion_graph.add_edge('bitter', 'indignant')
            self.emotion_graph.add_edge('bitter', 'violated')
            self.emotion_graph.add_edge('mad', 'furious')
            self.emotion_graph.add_edge('mad', 'jealous')
            self.emotion_graph.add_edge('aggressive', 'provoked')
            self.emotion_graph.add_edge('aggressive', 'hostile')
            self.emotion_graph.add_edge('frustrated', 'infuriated')
            self.emotion_graph.add_edge('frustrated', 'annoyed')
            self.emotion_graph.add_edge('distant', 'withdrawn')
            self.emotion_graph.add_edge('distant', 'numb')
            self.emotion_graph.add_edge('critical', 'skeptical')
            self.emotion_graph.add_edge('critical', 'dismissive')
            
            #Add disgusted emotions
            self.emotion_graph.add_edge('disgusted', 'disapproving')
            self.emotion_graph.add_edge('disgusted', 'disappointed')
            self.emotion_graph.add_edge('disgusted', 'awful')
            self.emotion_graph.add_edge('disgusted', 'repelled')
            self.emotion_graph.add_edge('disapproving', 'judgemental')
            self.emotion_graph.add_edge('disapproving', 'embarrassed')
            self.emotion_graph.add_edge('disappointed', 'appalled')
            self.emotion_graph.add_edge('disappointed', 'revolted')
            self.emotion_graph.add_edge('awful', 'nauseated')
            self.emotion_graph.add_edge('awful', 'detestable')
            self.emotion_graph.add_edge('repelled', 'horrified')
            self.emotion_graph.add_edge('repelled', 'hesitant')
            
            #Add sad emotions
            self.emotion_graph.add_edge('sad', 'hurt')
            self.emotion_graph.add_edge('sad', 'depressed')
            self.emotion_graph.add_edge('sad', 'guilty')
            self.emotion_graph.add_edge('sad', 'despair')
            self.emotion_graph.add_edge('sad', 'vulnerable')
            self.emotion_graph.add_edge('sad', 'lonely')
            self.emotion_graph.add_edge('hurt', 'embarrassed')
            self.emotion_graph.add_edge('hurt', 'disappointed')
            self.emotion_graph.add_edge('depressed', 'inferior')
            self.emotion_graph.add_edge('depressed', 'empty')
            self.emotion_graph.add_edge('guilty', 'remorseful')
            self.emotion_graph.add_edge('guilty', 'ashamed')
            self.emotion_graph.add_edge('despair', 'powerless')
            self.emotion_graph.add_edge('despair', 'grief')
            self.emotion_graph.add_edge('vulnerable', 'fragile')
            self.emotion_graph.add_edge('vulnerable', 'victimised')
            self.emotion_graph.add_edge('lonely', 'abandoned')
            self.emotion_graph.add_edge('lonely', 'isolated')

            #Add happy emotions
            self.emotion_graph.add_edge('happy', 'playful')
            self.emotion_graph.add_edge('happy', 'content')
            self.emotion_graph.add_edge('happy', 'interested')
            self.emotion_graph.add_edge('happy', 'proud')
            self.emotion_graph.add_edge('happy', 'accepted')
            self.emotion_graph.add_edge('happy', 'powerful')
            self.emotion_graph.add_edge('happy', 'peaceful')
            self.emotion_graph.add_edge('happy', 'trusting')
            self.emotion_graph.add_edge('happy', 'optimistic')
            self.emotion_graph.add_edge('playful', 'aroused')
            self.emotion_graph.add_edge('playful', 'cheeky')
            self.emotion_graph.add_edge('content', 'free')
            self.emotion_graph.add_edge('content', 'joyful')
            self.emotion_graph.add_edge('interested', 'curious')
            self.emotion_graph.add_edge('interested', 'inquisitive')
            self.emotion_graph.add_edge('proud', 'successful')
            self.emotion_graph.add_edge('proud', 'confident')
            self.emotion_graph.add_edge('accepted', 'respected')
            self.emotion_graph.add_edge('accepted', 'valued')
            self.emotion_graph.add_edge('powerful', 'courageous')
            self.emotion_graph.add_edge('powerful', 'creative')
            self.emotion_graph.add_edge('peaceful', 'loving')
            self.emotion_graph.add_edge('peaceful', 'thankful')
            self.emotion_graph.add_edge('trusting', 'sensitive')
            self.emotion_graph.add_edge('trusting', 'intimate')
            self.emotion_graph.add_edge('optimistic', 'hopeful')
            self.emotion_graph.add_edge('optimistic', 'inspired')
            
            file = nx.readwrite.write_gml(self.emotion_graph, emotion_graph_path)
        return

    def tick(self, task_pool):
        idxlist = task.find_tasks('Heart', task_pool)
        for idx in idxlist:
            item = task_pool.pop(idx)
            task_pool.insert(idx, self.work_task(item))
        return task_pool
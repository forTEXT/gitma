import os
from IPython.display import clear_output
import catma_gitlab.catma_gitlab_classes as cg


def select_value(prop, value_list):
	print(f'Gebe den Value für die Property "{prop}" ein')
	for index, value in enumerate(value_list):
		print(f'Für "{value}" wähle: {index}')
	print('Oder gebe einen anderen Value ein. Zum Stoppen der Annotationen gebe "quit" ein.')
	value = input('Value Eingabe: ')
	return value


def display_text(an: cg.Annotation):
	print(
		an.pretext,
		'\n-------------\n',
		an.text, 
		'\n-------------\n',
		an.posttext,
		'\n\n'
	)


def annotate(ac_name:str, tag:str, prop:str, start_point:int, end_point:int):
	project = cg.CatmaProject(os.listdir()[0])
	for ac in project.annotation_collections:
		if ac.name == ac_name:
			for an in ac.annotations[start_point: end_point]:
				if an.tag.name == tag:
					print(ac.text.title, '\n\n')
					display_text(an=an)
						
					value_list = an.tag.properties_dict[prop].possible_value_list
					value = select_value(prop, value_list)
						
					if value in [str(i) for i in range(len(value_list))]:
						an.modify_property_values(tag=tag, prop=prop, value=value_list[int(value)])
					elif value == 'quit':
						print('Annotation gestoppt.')
						break
					else:
						an.modify_property_values(prop=prop, value=value)
						
					clear_output(wait=True)


if __name__ == '__main__':
	ac_name = 'test_collection_1'
	tag = 'process'
	prop = 'mental'
	start_point = 0
	end_point = 10
	annotate(ac_name=ac_name, tag=tag, prop=prop, start_point=start_point, end_point=end_point)

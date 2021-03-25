from IPython.display import clear_output
import catma_gitlab.catma_gitlab_classes as cg


def select_value(prop, value_list):
	"""
	Used in annotate()
	"""
	print(f'Select Value for Property "{prop}"')
	for index, value in enumerate(value_list):
		print(f'For "{value}" choose: {index}')
	print('Or choose "quit".')
	value = input('Value Input: ')
	return value


def display_text(an: cg.Annotation):
	"""
	Used in annotate()
	"""
	print(
		an.pretext,
		'\n-------------\n',
		an.text, 
		'\n-------------\n',
		an.posttext,
		'\n\n'
	)


def annotate(project_uuid: str, ac_name: str, tag: str, prop: str, start_point: int, end_point: int):
	"""
	Function to annotate annotation tag properties in Jupyter Notebook.
	param: ac_name: CATMA Annotation Collection name (not the UUID)
	param: tag: Tag name. All annotations tagged by this tag can be modified.
	param: prop: Property name. Has to be a Property which is affiliated to definied Tag
	param: start_point: Annotation index to begin with
	param: end_point: Annotation index to end with
	"""
	project = cg.CatmaProject(project_uuid)
	ac = project.ac_dict[ac_name]
	tagged_annotations = [an for an in ac.annotations if an.tag.name == tag]

	if len(tagged_annotations) == 0:
		print('No annotations with tag found.')

	if start_point > len(tagged_annotations) or end_point > len(tagged_annotations):
		print('Start or end point is to high.')

	for an in tagged_annotations[start_point: end_point]:
		print(ac.text.title, '\n\n')
		display_text(an=an)

		value_list = an.tag.properties_dict[prop].possible_value_list
		value = select_value(prop, value_list)

		if value in [str(i) for i in range(len(value_list))]:
			an.set_property_values(tag=tag, prop=prop, value=value_list[int(value)])
		elif value == 'quit':
			print('Annotations stopped.')
			break
		else:
			an.set_property_values(prop=prop, value=value)

		clear_output(wait=True)


if __name__ == '__main__':
	pass

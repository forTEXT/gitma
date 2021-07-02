import os
import json
from catma_gitlab.text_class import Text
from catma_gitlab.tagset_class import Tagset
from catma_gitlab.annotation_collection_class import AnnotationCollection
from catma_gitlab.write_annotation import write_annotation_json, find_tag_by_name
from catma_gitlab.catma_gitlab_vizualize import plot_annotation_progression


def test_intrinsic(project_uuid: str, direction: str, test_positive=True):
    """
    This Function tests if a Catma Annotation Collection is intrinsic markup.
    :param project_uuid: CATMA gitlab root project uuids
    :param direction: annotation collection direction
    :param test_positive: what should be returned if it is intrinsic markup
    """
    with open(f'{project_uuid}/collections/{direction}/header.json', 'r') as header_input:
        header_dict = json.load(header_input)

    if header_dict['name'] == 'Intrinsic Markup':
        return test_positive


def test_empty_ac(root_direction, ac_id):
    if os.path.isdir(
            f'{root_direction}/collections/{ac_id}/annotations'):
        return True


class CatmaProject:
    def __init__(self, project_direction, root_direction, filter_intrinsic_markup=True):
        """
        Class which represents a CATMA project including the texts, the annotation collections and the tagsets using
        the classes Text, AnnotationCollection and Tagset.
        :param project_direction: direction where the project is located
        :param root_direction:  UUID of a CATMA project
        :param filter_intrinsic_markup: if False intrinsic markup is not filtered out, default=True
        """
        cwd = os.getcwd()                       # get the current direction to return after loaded the project
        self.project_direction = project_direction
        os.chdir(self.project_direction)
        self.uuid = root_direction

        # Load Tagsets
        tagsets_direction = root_direction + '/tagsets/'
        self.tagsets = [
            Tagset(
                root_direction=root_direction,
                catma_id=direction
            ) for direction in os.listdir(tagsets_direction)
        ]
        self.tagset_dict = {tagset.name: tagset for tagset in self.tagsets}

        # Load Texts
        texts_direction = root_direction + '/documents/'
        self.texts = [
            Text(
                root_direction=root_direction,
                catma_id=direction
            ) for direction in os.listdir(texts_direction)
        ]
        self.text_dict = {text.title: text for text in self.texts}

        # Load Annotation Collections
        collections_direction = root_direction + '/collections/'
        self.annotation_collections = [
            AnnotationCollection(
                root_direction=root_direction,
                catma_id=direction
            ) for direction in os.listdir(collections_direction)
            if test_empty_ac(                   # test if any annotation exist in annotation collectio
                root_direction,
                direction
                # test whether intrinsic markup is to be loaded
            ) and not test_intrinsic(
                root_direction,
                direction,
                filter_intrinsic_markup
            )
        ]
        self.ac_dict = {
            an_co.name: an_co for an_co in self.annotation_collections}

        os.chdir(cwd)

    def write_annotation(
            self, annotation_collection_name: str, tagset_name: str, text_title: str, tag_name: str,
            start_points: list, end_points: list, property_annotations: dict, author: str):
        os.chdir(self.project_direction)
        write_annotation_json(
            project_uuid=self.uuid,
            annotation_collection=self.ac_dict[annotation_collection_name],
            tagset=self.tagset_dict[tagset_name],
            text=self.text_dict[text_title],
            tag=find_tag_by_name(self.tagset_dict[tagset_name], tag_name),
            start_points=start_points,
            end_points=end_points,
            property_annotations=property_annotations,
            author=author
        )

    def iaa(self, ac1: str, ac2: str, tag_filter=None, filter_both_ac=False, level='tag'):
        """
        Computes Cohen's Kappa and Krippendorf's Alpha for 2 Annotation Collections.
        """
        from catma_gitlab.catma_gitlab_metrics import get_iaa
        get_iaa(
            ac1=self.ac_dict[ac1],
            ac2=self.ac_dict[ac2],
            tag_filter=tag_filter,
            filter_both_ac=filter_both_ac,
            level=level
        )

    def plot_progression(self, ac_filter: list = None):
        plot_annotation_progression(self, ac_filter=ac_filter)

    def import_document(self, direction: str, metadata: dict):
        """
        :param direction
        :param metadata: dictionary with document
        """
        pass


if __name__ == '__main__':
    project_direction = '../../catma_backup2'
    project_uuid = 'CATMA_DD5E9DF1-0F5C-4FBD-B333-D507976CA3C7_EvENT_root'
    project = CatmaProject(
        project_direction=project_direction,
        root_direction=project_uuid,
        filter_intrinsic_markup=False)

    project.plot_progression(ac_filter=['Effi_Briest_MW', 'Effi_Briest_GS'])

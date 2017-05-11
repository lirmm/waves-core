""" Retrieve runner list """
from __future__ import unicode_literals


def get_runners_list(flat=False):
    """
    Retrieve enabled waves.adaptors list from waves settings env file
    :return: a list of Tuple 'value'/'label'
    """
    from waves.addons.loader import load_core, load_extra_adaptors
    grp_impls = {'': 'Select a implementation class...'}
    grp_name = "WAVES Core"
    grp_impls[grp_name] = []
    for adaptor in load_core():
        grp_impls[grp_name].append(('.'.join((adaptor[1].__module__, adaptor[1].__name__)), adaptor[0]))
    for adaptor in load_extra_adaptors():
        grp_name = adaptor[1].__module__.split('.')[2].title()
        if grp_name not in grp_impls:
            grp_impls[grp_name] = []
        grp_impls[grp_name].append(('.'.join((adaptor[1].__module__, adaptor[1].__name__)), adaptor[0]))
    final = sorted((grp_key, grp_val) for grp_key, grp_val in grp_impls.items())
    if not flat:
        return sorted(final, key=lambda tup: tup[0])
    else:
        flattened = []
        for elem in final:
            if type(elem[1]) is list:
                for clazz in elem[1]:
                    flattened.append(clazz)
        return flattened

runner_list = get_runners_list()

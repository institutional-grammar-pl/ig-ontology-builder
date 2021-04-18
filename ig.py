import logging
import re
import types
from collections import defaultdict

import lemminflect
import owlready2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


constitutive_columns = [
    "Constituted Entity (Content)",
    "Constituted Entity Property (Content)",
    "Constituted Entity Property (Reference to statement)",
    "Modal",
    "Function",
    "Constituted Properties (Content)",
    "Constituted Properties (Reference to statement)",
    "Constituted Properties Property (Content)",
    "Constituted Properties Property (Reference to statement)",
    "Activation Condition (Content)",
    "Activation Condition (Reference to statement)",
    "Execution Constraint (Content)",
    "Execution Constraint (Reference to statement)",
    "Or else (Forward reference to consequential statement)",
    "Logical combination",
]

regulative_columns = [
    "Attributes (Content)",
    "Attributes property (Content)",
    "Attributes property (Reference to statement)",
    "Deontic",
    "Aim",
    "Direct Object (Content)",
    "Direct Object (Reference to statement)",
    "Direct Object Property",
    "Indirect Object",
    "Indirect Object Property",
    "Activation Condition (Content)",
    "Activation Condition (Reference to statement)",
    "Execution Constraint (Content)",
    "Execution Constraint (Reference to statement)",
    "Or else (Reference to consequential statement)",
    "Logical combination",
]
original_relation_to_relation = defaultdict(dict)


def check_observations_constraints(df_observations):
    problematic_stmts = list(df_observations[df_observations[ACT_COND] != ""][STMT_NO])
    if len(problematic_stmts) > 0:
        logger.warning(
            f"There are observations with non-empty activation condition {problematic_stmts}"
        )


def get_relation_name(semantic_relation_name, subject):
    a = original_relation_to_relation.get(semantic_relation_name)
    if a is not None:
        b = a.get(subject)
        if b is not None:
            return b
    return semantic_relation_name


both = ["Statement function", "Statement No.", "Statement"]
CLASS = "IG syntax (regulative, constitutive)"
STMT_FUNCTION = "Statement function"

CON_PROP = "Constituted Properties (Content)"
CON_PROP_PROP = "Constituted Properties Property (Content)"
CON_FUNC = "Function"
ENT = "Constituted Entity (Content)"
ENT_PROP = "Constituted Entity Property (Content)"


ATTR = "Attributes (Content)"
ATTR_PROP = "Attributes property (Content)"

DIR_OBJ = "Direct Object (Content)"
DIR_OBJ_PROP = "Direct Object Property"

INDIR_OBJ = "Indirect Object"
INDIR_OBJ_PROP = "Indirect Object Property"

DEON = "Deontic"
AIM = "Aim"

FUN = "Function"
MODAL = "Modal"

ACT_COND = "Activation Condition (Content)"

ENT_PROP_REF = "Constituted Entity Property (Reference to statement)"
CON_PROP_REF = "Constituted Properties (Reference to statement)"
CON_PROP_PROP_REF = "Constituted Properties Property (Reference to statement)"
ACT_COND_REF = "Activation Condition (Reference to statement)"

ATTR_PROP_REF = "Attributes property (Reference to statement)"
DIR_OBJ_REF = "Direct Object (Reference to statement)"

STMT = "Statement"
STMT_NO = "Statement No."
onto = owlready2.get_ontology("ig.onto.owl")


def get_class(name):
    return onto[fix_class_name(name)]


def fix_class_name(name):
    # TODO: fix
    name = name.lower()
    name = name.replace("-", " ")
    name = name.replace("and[each,", "")
    name = name.replace("and[any", "")
    name = name.replace("|", "")
    name = name.replace("[", "").replace("]", "")
    name = name.replace("the", "")
    return name.title().replace(" ", "")


def fix_relation_name(name: str) -> str:
    return name.replace(" ", "_")


def create_base_class(name):
    name = fix_class_name(name)
    if name == "":
        return None
    with onto:
        new_class = types.new_class(name, (owlready2.Thing,))
    return new_class


def create_class(name, superclass):
    if superclass is None:
        raise TypeError(f"superclass of ({name}) is missing")
    name = fix_class_name(name)
    if name == "":
        return None
    new_class = types.new_class(name, (superclass,))

    return new_class


statement_no_to_realtion = defaultdict(list)


def define_relationship(
    subject,
    relation_name,
    object,
    statement_no,
    relation_constraint="",
    unique_relation=True,
):
    comments = []
    relation_name = fix_relation_name(relation_name)
    original_relation = relation_name
    if unique_relation:
        while onto[relation_name] is not None:
            if subject in onto[relation_name].domain:
                # if there is relation with same subject, update it subject
                logger.debug(f"Relation {relation_name} exsits. Updating...")
                comments = onto[relation_name].comment
                break
            relation_name += "'"
            logger.debug(f"Relation {relation_name} already exsits, appending '")
        original_relation_to_relation[original_relation][subject] = relation_name

    else:
        relation = onto[relation_name]
        if relation is not None:
            logger.debug(f"Relation {relation} exsits. Updating...")
            comments = relation.comment

    logger.debug(f"Defining relation {subject} - {relation_name} - {object}")

    with onto:
        relation = types.new_class(relation_name, (subject >> object,))
        if relation_constraint == "some":
            relation.class_property_type = ["some"]
        # relation.comment = []
        if statement_no is not None:
            relation.comment = comments
            relation.comment.append(f"From statement: {statement_no}")
            relation.comment = ["\n".join(relation.comment)]

    statement_no_to_realtion[statement_no].append((subject, relation_name, object))


def get_passive(verb):
    return lemminflect.getInflection(verb, tag="VBD")[0]


def get_passive_deontic_relation_name(deontic, aim):
    return " ".join([deontic, "be", get_passive(aim), "to"])


def get_passive_relation_name(aim):
    return " ".join(["is", get_passive(aim)])


illegal_regex = r"AND\[[\d\.,]+\]"


def report_annotation_error(row_num, error):
    logger.warning(f"Possible anotation error in row {row_num} ({error})")


def report_missing(subj, obj, stmt_no):
    logger.warning(
        f"Object or subject is missing in {stmt_no}: Subject({subj}), Object({obj})"
    )


def create_classes_from_df(subclasses_df, connector_word=None):
    created_classes = []
    for id, row in subclasses_df.iterrows():
        try:
            superclass_name = row[0]
            if re.search(illegal_regex, superclass_name):
                report_annotation_error(id, superclass_name)

            superclass = get_class(superclass_name)
            if superclass is None:
                superclass = create_base_class(superclass_name)

            if connector_word is not None:
                subclass_name = " ".join([row[0], connector_word, *row[1:]])
            else:
                subclass_name = " ".join(row)
            if re.search(illegal_regex, " ".join(row[1:])):
                report_annotation_error(id, " ".join(row[1:]))

            if row[1] != "":  # do not create empty
                subclass = create_class(subclass_name, superclass)
            else:
                subclass = None
            created_classes.append((superclass, subclass))
        except TypeError as e:
            logger.warning(e)
    return set(created_classes)


def create_relations_from_regulative_aim(
    df_subject, df_relation, df_object, df_indir_object, stmt_nos
):
    forward_relations = 0
    passive_relations = 0
    for (_, subj_row), (_, rel_row), (_, obj_row), (_, iobj_row), stmt_no in zip(
        df_subject.iterrows(),
        df_relation.iterrows(),
        df_object.iterrows(),
        df_indir_object.iterrows(),
        stmt_nos,
    ):
        subj = get_class(" ".join(subj_row))
        obj = get_class(" ".join(obj_row))
        relation_name = fix_relation_name(" ".join(rel_row))
        deontic = rel_row[DEON]
        aim = rel_row[AIM]
        if not (subj is None or obj is None):
            define_relationship(subj, relation_name, obj, statement_no=stmt_no)
            forward_relations += 1
            indir_obj = get_class(" ".join(iobj_row))
            if not (indir_obj is None or obj is None):
                passive_relations += 1
                passive_relation = get_passive_deontic_relation_name(deontic, aim)
                define_relationship(
                    obj, passive_relation, indir_obj, statement_no=stmt_no
                )
        else:
            report_missing(subj, obj, stmt_no)
    logger.info("Forward relations defined: " + str(forward_relations))
    logger.info("Passive relations defined: " + str(passive_relations))


def create_relations_from_obserations_aim_from_df(df):
    forward_relations = 0
    passive_relations = 0
    for _, row in df.iterrows():
        attr = row[ATTR]
        attrs_prop = row[ATTR_PROP]
        aim = row[AIM]
        dir_obj = row[DIR_OBJ]
        dir_obj_prop = row[DIR_OBJ_PROP]
        indir_obj = row[INDIR_OBJ]
        indir_obj_prop = row[INDIR_OBJ_PROP]
        stmt_no = row[STMT_NO]

        subj = get_class(" ".join([attr, attrs_prop]))
        obj = get_class(" ".join([dir_obj, dir_obj_prop]))
        relation_name = fix_relation_name(aim)
        if not (subj is None or obj is None):
            define_relationship(
                subj, relation_name, obj, statement_no=stmt_no, unique_relation=False
            )
            forward_relations += 1
            indirect_object = get_class(" ".join([indir_obj, indir_obj_prop]))
            if indirect_object is not None:
                passive_relations += 1
                passive_relation = get_passive_relation_name(aim)
                define_relationship(
                    obj,
                    passive_relation,
                    indirect_object,
                    statement_no=stmt_no,
                    unique_relation=False,
                )
        else:
            report_missing(subj, obj, stmt_no)


def create_constitutive_modal_function_relations_from_df(df):
    for _, row in df.iterrows():
        subj = get_class(" ".join(row[[ENT, ENT_PROP]]))
        obj = get_class(" ".join(row[[CON_PROP, CON_PROP_PROP]]))
        statement_no = row[STMT_NO]
        modal = row[MODAL]
        function = row[FUN]
        relation_name = " ".join([modal, function]) if modal != "" else function
        relation_name = fix_relation_name(relation_name)
        if not (subj is None or obj is None):
            define_relationship(
                subj,
                relation_name,
                obj,
                statement_no=statement_no,
                unique_relation=True,
            )
        else:
            report_missing(subj, obj, statement_no)

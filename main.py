import logging

import pandas as pd
import typer

import ig
from ig import both, constitutive_columns, create_classes_from_df, regulative_columns
from rules import define_activation_condition_rules_from_df

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main(input_annotation_path: str, output_ontology_path: str = "ig.owl"):
    # pd.set_option("display.max_colwidth", None)
    # pd.set_option("display.max_rows", None)
    # pd.set_option("display.max_columns", None)
    df = pd.read_excel(
        input_annotation_path,
        skiprows=1,
        dtype=str,
    )
    # preprocessign df
    df = df.fillna("")
    df = df.applymap(lambda t: t.strip() if type(t) == str else t)
    ig.check_duplicates(df)
    df2 = df[
        [
            "Activation Condition (Content).1",
            "Activation Condition (Reference to statement).1",
            "Execution Constraint (Content).1",
            "Execution Constraint (Reference to statement).1",
        ]
    ]
    df2 = df2.rename(
        {
            a: a[:-2]
            for a in [
                "Activation Condition (Content).1",
                "Activation Condition (Reference to statement).1",
                "Execution Constraint (Content).1",
                "Execution Constraint (Reference to statement).1",
            ]
        },
        axis=1,
    )
    cols = [
        "Activation Condition (Content)",
        "Activation Condition (Reference to statement)",
        "Execution Constraint (Content)",
        "Execution Constraint (Reference to statement)",
    ]
    for c in cols:
        df.loc[df2[c] != "", c] = df2[c]

    logger.info(
        f"Loaded activation conditions(references): {sum(df[ig.ACT_COND_REF]!='')}"
    )
    constitutive = df[df[ig.CLASS] == "constitutive"][constitutive_columns + both]
    regulative = df[df[ig.CLASS] == "regulative"][regulative_columns + both]
    df_constitutive = constitutive[constitutive[ig.STMT_FUNCTION] == "constitutive"]
    df_observations = constitutive[constitutive[ig.STMT_FUNCTION] == "observation"]
    df_reg_observation = regulative[regulative[ig.STMT_FUNCTION] == "observation"]
    df_regulative = regulative[regulative[ig.STMT_FUNCTION] == "regulative"]

    # Cheks
    ig.check_observations_constraints(df_observations)
    ig.check_observations_constraints(df_reg_observation)

    # # Constitutive
    # ## Constitutive -- observations
    create_classes_from_df(
        df_observations[[ig.ENT, ig.CON_FUNC, ig.CON_PROP, ig.CON_PROP_PROP]],
        statement_nos=df_observations[ig.STMT_NO],
        connector_word="that",
    )
    # ## Constitutive -- proper
    df_constitutive = df_constitutive[df_constitutive[ig.ENT] != ""]
    # ### Constitutive -- proper: entities
    create_classes_from_df(
        df_constitutive[[ig.ENT, ig.ENT_PROP]],
        df_constitutive[ig.STMT_NO],
        class_type=ig.ENT,
    )
    # ### Constitutive -- proper: Constituted Properties
    create_classes_from_df(
        df_constitutive[[ig.CON_PROP, ig.CON_PROP_PROP]],
        df_constitutive[ig.STMT_NO],
        class_type=ig.CON_PROP,
    )
    # # Regulative statements
    # ## Regulative -- observations
    # ### Regulative -- observations: attr
    create_classes_from_df(
        df_reg_observation[[ig.ATTR, ig.ATTR_PROP]],
        df_reg_observation[ig.STMT_NO],
        class_type=ig.ATTR,
    )
    # ### Regulative -- observations: direct object
    create_classes_from_df(
        df_reg_observation[[ig.DIR_OBJ, ig.DIR_OBJ_PROP]],
        df_reg_observation[ig.STMT_NO],
        class_type=ig.DIR_OBJ,
    )
    # ### Regulative -- observations: indirect objects
    create_classes_from_df(
        df_reg_observation[[ig.INDIR_OBJ, ig.INDIR_OBJ_PROP]],
        df_reg_observation[ig.STMT_NO],
        class_type=ig.INDIR_OBJ,
    )
    # ## Regulative -- proper regulative
    # ### Regulative -- observations: attr
    create_classes_from_df(
        df_regulative[[ig.ATTR, ig.ATTR_PROP]],
        df_regulative[ig.STMT_NO],
        class_type=ig.ATTR,
    )
    # ### Regulative -- objects
    create_classes_from_df(
        df_regulative[[ig.DIR_OBJ, ig.DIR_OBJ_PROP]],
        df_regulative[ig.STMT_NO],
        class_type=ig.DIR_OBJ,
    )
    # ### Regulative -- indirect objects
    create_classes_from_df(
        df_regulative[[ig.INDIR_OBJ, ig.INDIR_OBJ_PROP]],
        df_regulative[ig.STMT_NO],
        class_type=ig.INDIR_OBJ,
    )
    ig.statement_no_to_constituted_subclass = dict(
        ig.statement_no_to_constituted_subclass
    )  # froze dict
    # # Relations extraction
    # ### Regulative -- observations:  possible (aim) relations
    ig.create_relations_from_obserations_aim_from_df(df_reg_observation)
    # ### Regulative (aim) relations
    ig.create_relations_from_regulative_aim(
        df_regulative[[ig.ATTR, ig.ATTR_PROP]],
        df_regulative[[ig.DEON, ig.AIM]],
        df_regulative[[ig.DIR_OBJ, ig.DIR_OBJ_PROP]],
        df_regulative[[ig.INDIR_OBJ, ig.INDIR_OBJ_PROP]],
        df_regulative[ig.STMT_NO],
    )
    # ### Constitutive (modal, function) relations
    ig.create_constitutive_modal_function_relations_from_df(df_constitutive)

    # Defining rules
    # ## Activation conditions
    define_activation_condition_rules_from_df(df_regulative)
    define_activation_condition_rules_from_df(df_constitutive)

    ig.onto.save(output_ontology_path)


if __name__ == "__main__":
    typer.run(main)

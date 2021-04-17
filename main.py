#!/usr/bin/env python
# coding: utf-8
import pandas as pd

import ig
from ig import both, constitutive_columns, create_classes_from_df, regulative_columns

pd.set_option("display.max_colwidth", None)
pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
df = pd.read_excel("2021.04.16_all_H.R.6201_Emergency_Paid_Sick_Leave.xlsx", skiprows=1)
# preprocessign df
df = df.fillna("")
df = df.applymap(lambda t: t.strip() if type(t) == str else t)
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
constitutive = df[df[ig.CLASS] == "constitutive"][constitutive_columns + both]
regulative = df[df[ig.CLASS] == "regulative"][regulative_columns + both]
df_constitutive = constitutive[constitutive[ig.STMT_FUNCTION] == "constitutive"]
df_observations = constitutive[constitutive[ig.STMT_FUNCTION] == "observation"]
# # Constitutive
## Constitutive -- observations
create_classes_from_df(
    df_observations[
        [ig.ENT, ig.CON_FUNC, ig.CON_PROP, ig.CON_PROP_PROP]
    ].drop_duplicates(),
    connector_word="that",
)
## Constitutive -- proper
df_constitutive = df_constitutive[df_constitutive[ig.ENT] != ""]
create_classes_from_df(df_constitutive[[ig.ENT, ig.ENT_PROP]])
create_classes_from_df(df_constitutive[[ig.CON_PROP, ig.CON_PROP_PROP]])
...
df_constitutive[[ig.CON_PROP, ig.CON_PROP_PROP]]
df[df[ig.STMT_NO] == 34.2]
# # Regulative statements
df_reg_observation = regulative[regulative[ig.STMT_FUNCTION] == "observation"]
df_regulative = regulative[regulative[ig.STMT_FUNCTION] == "regulative"]
# ## Regulative -- observations
# ### Regulative -- observations: attr
create_classes_from_df(df_reg_observation[[ig.ATTR, ig.ATTR_PROP]])
# ### Regulative -- observations: direct object
create_classes_from_df(df_reg_observation[[ig.DIR_OBJ, ig.DIR_OBJ_PROP]])
# ### Regulative -- observations: indirect objects
create_classes_from_df(df_reg_observation[[ig.INDIR_OBJ, ig.INDIR_OBJ_PROP]])
# ## Regulative -- proper regulative
# ### Regulative -- observations: attr
_ = create_classes_from_df(df_regulative[[ig.ATTR, ig.ATTR_PROP]])
# ### Regulative -- objects
_ = create_classes_from_df(df_regulative[[ig.DIR_OBJ, ig.DIR_OBJ_PROP]])
# ### Regulative -- indirect objects
_ = create_classes_from_df(df_regulative[[ig.INDIR_OBJ, ig.INDIR_OBJ_PROP]])
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
ig.onto.save("ig.owl")
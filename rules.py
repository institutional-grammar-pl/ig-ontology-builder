import logging

import owlready2

import ig

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def get_act_cond(act_cond_str):
    if act_cond_str[:2] == "OR":
        return act_cond_str[3:-1].split(",")
    if act_cond_str[:3] == "AND":
        return act_cond_str
    else:
        return act_cond_str.strip("[]")


def get_rule(sub, rel, obj, concl_sub, concl_rel, concl_obj, negation=False):
    s1, s2, o1, o2 = "?x", "?y", "?z", "?q"
    if sub == concl_sub:
        s1 = s2
    if sub == concl_obj:
        s1 = o2
    if obj == concl_obj:
        o1 = o2
    if obj == concl_sub:
        o1 = s2
    return f"{sub}({s1}), {obj}({o1}), {rel}({s1}, {o1}), {concl_sub}({s2}), {concl_obj}({o2}) -> {concl_rel}({s2},{o2})"


def get_rules_from_statements(
    activation_condition_stmt_no, colclusion_stmt_no, negation=False
):
    logger.debug("get_rules_from_statements")
    rules = []
    for concl_subj, concl_rel, concl_obj in ig.statement_no_to_realtion[
        colclusion_stmt_no
    ]:
        for subj, relation, obj in ig.statement_no_to_realtion[
            activation_condition_stmt_no
        ]:
            rules.append(
                get_rule(
                    subj.name,
                    relation,
                    obj.name,
                    concl_subj.name,
                    concl_rel,
                    concl_obj.name,
                    negation=negation,
                )
            )

    for rule in rules:
        add_rule(rule)


def add_rule(rule_str):
    logger.info(f"adding rule: {rule_str}")
    with ig.onto:
        rule = owlready2.Imp()
        rule.set_as_rule(rule_str)


def define_rules(act_cond, stmt_no, negation=False):
    if act_cond == "":
        return
    act_cond = get_act_cond(act_cond)
    if type(act_cond) == list:
        for a_cond in act_cond:
            define_rules(a_cond, stmt_no)
    else:
        if act_cond[:3] == "NOT":
            ...
            # TODO
        #             act_cond = act_cond.strip("NOT ")
        #             define_rules(act_cond, stmt_no, negation=(not negation))
        else:
            act_cond = float(act_cond)
            get_rules_from_statements(act_cond, stmt_no, negation=negation)


def define_activation_condition_rules_from_df(df):
    for act_cond, stmt_no in zip(df[ig.ACT_COND_REF], df[ig.STMT_NO]):
        define_rules(act_cond, stmt_no)

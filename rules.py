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


def _check_subclasses(a, b):
    if a is None or b is None:
        return False
    return a == b or issubclass(a, b) or issubclass(b, a)


def get_rule(sub, rel, obj, concl_sub, concl_rel, concl_obj, negation=False):
    s1, s2, o1, o2 = "?x", "?y", "?z", "?q"
    if _check_subclasses(sub, concl_sub):
        s1 = s2
    if _check_subclasses(sub, concl_obj):
        s1 = o2
    if _check_subclasses(obj, concl_obj):
        o1 = o2
    if _check_subclasses(obj, concl_sub):
        o1 = s2
    if rel is not None:
        rule = f"{sub.name}({s1}), {obj.name}({o1}), {concl_sub.name}({s2}), {concl_obj.name}({o2}), {rel}({s1}, {o1}) -> {concl_rel}({s2},{o2})"
    else:
        rule = f"{sub.name}({s1}), {concl_sub.name}({s2}), {concl_obj.name}({o2}) -> {concl_rel}({s2},{o2})"
    return rule


def get_rules_from_statements(
    activation_condition_stmt_no, colclusion_stmt_no, negation=False
):
    logger.debug("get_rules_from_statements")
    rules = []
    conclusion_relations = ig.statement_no_to_realtion[colclusion_stmt_no]
    activation_relations = ig.statement_no_to_realtion[activation_condition_stmt_no]
    if len(conclusion_relations) == 0:
        logger.warning(
            f"No conclusion relations found for statement({colclusion_stmt_no})"
        )
    if len(activation_relations) == 0:
        logger.info(
            f"No activation relations found for statement ({activation_condition_stmt_no}). Checking subclasses"
        )
        subclass_subj = ig.statement_no_to_constituted_subclass[
            activation_condition_stmt_no
        ]["default"]
        relation = None
    else:
        subclass_subj = None

    for concl_subj, concl_rel, concl_obj in conclusion_relations:
        if subclass_subj is None:
            for subj, relation, obj in activation_relations:
                rules.append(
                    get_rule(
                        subj,
                        relation,
                        obj,
                        concl_subj,
                        concl_rel,
                        concl_obj,
                        negation=negation,
                    )
                )
        else:
            rules.append(
                get_rule(
                    subclass_subj,
                    None,
                    None,
                    concl_subj,
                    concl_rel,
                    concl_obj,
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
            # act_cond = float(act_cond)
            get_rules_from_statements(act_cond, stmt_no, negation=negation)


def define_activation_condition_rules_from_df(df):
    for act_cond, stmt_no in zip(df[ig.ACT_COND_REF], df[ig.STMT_NO]):
        define_rules(act_cond, stmt_no)

# ids.py
# Ronald L. Rivest (with Karim Husayn Karimi)
# July 24, 2017
# python3

"""
Routines in support of audit program multi.py.
These routines all related to ids:
    contest ids (cids)
    paper ballot collection ids (pbcids)
    selection ids (selids)
    ballot ids (bids)
    measurement ids (mids)
"""

##############################################################################
## generic id-related routines


def clean_id(id):
    """ 
    Return id with initial and final whitespace removed, and
    with any internal whitespace sequences replaced by a single
    blank.  Also, all nonprintable characters are removed.
    """

    id = id.strip()
    new_id = ""
    for c in id:
        if c.isspace():
            c = " "
        if (c != " " or (len(new_id)>0 and new_id[-1] != " ")) \
           and c.isprintable():
            new_id += c
    return new_id


def filename_safe(id):
    """
    Remove all characters other than letters, digits, hyphen, underscore, and plus.
    """

    ans = []
    for c in id:
        if c.isalnum() or c in "+-_":
            ans.append(c)
    return "".join(ans)

    
##############################################################################
## selid-specifc routines


def is_writein(selid):

    return len(selid) > 0 and selid[0] == "+"


def is_error_selid(selid):

    return len(selid) > 0 and selid[0] == "-"










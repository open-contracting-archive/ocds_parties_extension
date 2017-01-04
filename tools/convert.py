# This function will convert data from 1.0 to 1.1 with respect to parties
import sys # Needed during testing - update later
import ijson #Only needed during testing - update later
import optparse
from copy import deepcopy
import hashlib
import json


# Update the parties array and return an updated organisation reference block to use.
def generate_party(parties,org,role=[]):

    # If we have a schema AND id, we can generate a suitable ID
    try:
        if len(org['identifier']['id']) > 0:
            orgid = org['identifier']['id']
        else:
            raise Exception("No identifier was found")

        if len(org['identifier']['scheme']) > 2 and len(org['identifier']['scheme']) < 20:
            scheme = org['identifier']['scheme']
        else:
            raise Exception("Schemes need to be between 2 and 20 characters")

        identifier = scheme + "-" + orgid

    # Otherwise we generate an ID based on a hash of the who organisation object 
    # ToDo: Check if we should do this from name instead...
    except Exception as err:
        identifier = hashlib.md5(json.dumps(org).encode('utf8')).hexdigest()

    # Then we check if this organisation was already in the parties array
    if parties.get(identifier,False):
        # If it is there, but the organisation name and contact point doesn't match, we need to add a separate organisation entry for this sub-unit or department
        if not(parties.get(identifier).get('name','') == org.get('name','')) or not(parties.get(identifier).get('contactPoint','') == org.get('contactPoint','')):
            identifier = identifier + "-" + hashlib.md5(json.dumps(org.get('name','')).encode('utf8') + json.dumps(org.get('contactPoint','')).encode('utf8')).hexdigest() 

    # Now we fetch existing list of roles and merge 
    roles = parties.get(identifier,{}).get('roles',[])
    org['roles'] = list(set(roles + role))

    # And we add the identifier to the organisation object before adding/updated the parties object
    org['id'] = identifier
    parties[identifier] = deepcopy(org)

    
    if backwards_compatible:
        org.pop('roles')
        return org
    else:
        return { "id":identifier,"name":org.get('name','')}


# Expects a JSON object containing a release
def upgrade(release):
    ## First, create the parties array.
    parties = {}

    ## Update procuringEntity
    try:
        release['buyer'] = generate_party(parties, release['buyer'], ['buyer'])
    except Exception as err:
        pass

    ## Update procuringEntity
    try:
        release['tender']['procuringEntity'] = generate_party(parties, release['tender']['procuringEntity'], ['procuringEntity'])
    except Exception as err:
        pass

    # Update tenderers
    try: 
        for num, tenderer in enumerate(release['tender']['tenderers']):
            release['tender']['tenderers'][num] = generate_party(parties, tenderer, ['tenderer'])
    except Exception as err:
        pass

    # Update award and contract suppliers
    try: 
        for anum, award in enumerate(release['awards']):
            for snum, supplier in enumerate(release['awards'][anum]['suppliers']):
                release['awards'][anum]['suppliers'][snum] = generate_party(parties, supplier, ['supplier'])
    except Exception as err:
        pass

    # (Although contract suppliers is not in the standard, some implementations have been using this)
    try: 
        for anum, award in enumerate(release['contracts']):
            for snum, supplier in enumerate(release['contracts'][anum]['suppliers']):
                release['contracts'][anum]['suppliers'][snum] = generate_party(parties, supplier, ['supplier'])
    except Exception as err:
        pass

    # Now format the parties into a simple array
    release['parties'] = []
    for key in parties:
        release['parties'].append(parties[key])

    return release


def extract(file):
    releases = ijson.items(file, 'releases.item')
    for release in releases:
        print(json.dumps(upgrade(release),indent=4,ensure_ascii=False))


def main():
    usage = 'Usage: %prog [ --all --cont ]'
    parser = optparse.OptionParser(usage=usage)

    parser.add_option('-c','--compat', action='store_true', default=False,
                      help='If set, then include full organisation objects as well as references')

    (options, args) = parser.parse_args()
    backwards_compatible = options.compat
    global backwards_compatible

    extract(sys.stdin)

if __name__ == '__main__':
    main()


import cfscrape
import time
import os
import slugify
import json


ROOT = "https://www.pilipinaselectionresults2016.com/"
file_path = [os.path.abspath(os.curdir), 'data']
scraper = cfscrape.create_scraper()


def get_data(url, sleep_time=1):
    res = scraper.get(url)
    data = res.json()

    path_name = data.get('name')
    if path_name is not None:
        path_name = slugify.slugify(path_name)

    time.sleep(sleep_time)

    return data, path_name


def get_name(data):
    return data.get('name', 'No name...')


def save_data(data, file_path):
    path = os.path.join(*file_path)
    if not os.path.isdir(path):
        os.makedirs(path)

    fp = os.path.join(path, file_path[-1] + '.json')

    with open(fp, 'w') as fl:
        json.dump(data, fl)


def get_url(path):
    return ROOT + path


def get_subregions(data):
    return sorted(data.get('subRegions').keys())


def get_custom_code(data):
    return data.get('customCode')


def skip_tally(regional_json, subregional_json, municipality_json):
    # Use this to ignore already downloaded data
    skip_region = None
    skip_subregion = None
    skip_municipality = None

    if all([skip_region, regional_json]):
        if (get_custom_code(regional_json) < skip_region):
            return True

    if all([skip_region, skip_subregion, regional_json, subregional_json]):
        if (get_custom_code(regional_json) == skip_region) and (get_name(subregional_json) < skip_subregion):
            return True

    if all([skip_region, skip_subregion, skip_municipality, regional_json, subregional_json, municipality_json]):
        if (
            (get_custom_code(regional_json) == skip_region) and
            (get_name(subregional_json) == skip_subregion) and
            (get_name(municipality_json) < skip_municipality)
        ):
            return True

    return False


def process_data(parent_json, child_key, level=0, out_type='subRegions'):
    global file_path
    is_path_added = False

    child_url = get_url(parent_json.get('subRegions')[child_key].get('url'))
    child_json, path_name = get_data(child_url)

    print '\t' * level, get_name(child_json)

    if path_name is not None:
        file_path.append(path_name)
        is_path_added = True

    save_data(child_json, file_path)

    if out_type == 'subRegions':
        grandchildren = get_subregions(child_json)
    elif out_type == 'contests':
        grandchildren = child_json.get(out_type)
    else:
        raise ValueError('Use either `subRegions` or `contests` as out_type value.')

    return child_json, grandchildren, is_path_added


def process_contests(contests_list):
    global file_path

    if contests_list is None:
        return

    # Get actual poll results
    for contest in contests_list:
        contest_url = get_url(contest['url'])

        try:
            contest_json, _ = get_data(contest_url, sleep_time=0.1)
        except Exception as e:
            print e.message
            continue

        path_name = contest['url']
        file_path.append(path_name)
        fname = os.path.join(*file_path)

        if not os.path.exists(os.path.dirname(fname)):
            os.makedirs(os.path.dirname(fname))

        with open(fname, 'w') as fl:
            json.dump(contest_json, fl)

        file_path.pop()


class Depth(object):
    subregional = 0
    municipality = 1

# This can be used to indicate whether the scraper should scrape upto the municipality level or not.
MAX_DEPTH = Depth.municipality

if __name__ == '__main__':

    country_url = get_url("data/regions/0.json")
    country_json, path_name = get_data(country_url)
    print get_name(country_json)

    if path_name is not None:
        file_path.append(path_name)

    save_data(country_json, file_path)
    regions = get_subregions(country_json)

    for region in regions:
        print '\t', region
        regional_json, subregions, is_path_added = process_data(country_json, region, level=1)

        if skip_tally(regional_json, None, None):
            if is_path_added:
                file_path.pop()
            continue

        for subregion in subregions:
            subregional_json, municipalities, is_path_added = process_data(regional_json, subregion, level=2)

            if skip_tally(regional_json, subregional_json, None):
                if is_path_added:
                    file_path.pop()
                continue

            subregional_contests = subregional_json.get('contests')
            process_contests(subregional_contests)

            if MAX_DEPTH != Depth.municipality:
                file_path.pop()
                continue

            for municipality in municipalities:
                municipality_json, municipal_contests, is_path_added = (
                    process_data(
                        subregional_json,
                        municipality,
                        level=3,
                        out_type='contests'
                    )
                )

                if skip_tally(regional_json, subregional_json, municipality_json):
                    if is_path_added:
                        file_path.pop()
                    continue

                process_contests(municipal_contests)

                file_path.pop()

            file_path.pop()

        file_path.pop()

    file_path.pop()

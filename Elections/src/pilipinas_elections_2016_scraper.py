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


def skip_tally(regional_json, subregional_json, municipality_json):
    # Use this to ignore already downloaded data
    skip_region = 'REGION I'  # None
    skip_subregion = 'LA UNION'  # None
    skip_municipality = 'BANGAR'  # None

    if all([skip_region, regional_json]):
        if (get_name(regional_json) < skip_region):
            return True

    if all([skip_region, skip_subregion, regional_json, subregional_json]):
        if (get_name(regional_json) == skip_region) and (get_name(subregional_json) < skip_subregion):
            return True

    if all([skip_region, skip_subregion, skip_municipality, regional_json, subregional_json, municipality_json]):
        if (get_name(regional_json) == skip_region) and (get_name(subregional_json) == skip_subregion) and (get_name(municipality_json) < skip_municipality):
            return True

    return False


country_url = get_url("data/regions/0.json")
country_json, path_name = get_data(country_url)
print get_name(country_json)

if path_name is not None:
    file_path.append(path_name)

save_data(country_json, file_path)
regions = get_subregions(country_json)

for region in regions:
    regional_url = get_url(country_json.get('subRegions')[region].get('url'))

    regional_json, path_name = get_data(regional_url)
    print '\t', get_name(regional_json)

    if skip_tally(regional_json, None, None):
        continue

    if path_name is not None:
        file_path.append(path_name)

    save_data(regional_json, file_path)

    subregions = get_subregions(regional_json)

    for subregion in subregions:
        subregional_url = get_url(regional_json.get('subRegions')[subregion].get('url'))

        subregional_json, path_name = get_data(subregional_url)
        print '\t\t', get_name(subregional_json)

        if skip_tally(regional_json, subregional_json, None):
            continue

        if path_name is not None:
            file_path.append(path_name)

        save_data(subregional_json, file_path)

        municipalities = get_subregions(subregional_json)

        for municipality in municipalities:
            municipality_url = get_url(subregional_json.get('subRegions')[municipality].get('url'))

            municipality_json, path_name = get_data(municipality_url)
            print '\t\t\t', get_name(municipality_json)

            if skip_tally(regional_json, subregional_json, municipality_json):
                continue

            if path_name is not None:
                file_path.append(path_name)

            save_data(municipality_json, file_path)

            # Get actual poll results
            contests = municipality_json.get('contests')

            for contest in contests:
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

            file_path.pop()

        file_path.pop()

    file_path.pop()

file_path.pop()

import errno
from kungfu.yijinjing import *
from pykungfu import yijinjing as yjj

class Locator(yjj.locator):
    def __init__(self, home):
        yjj.locator.__init__(self)
        self._home = home

    def has_env(self, name):
        return os.getenv(name) is not None

    def get_env(self, name):
        return os.getenv(name)

    def layout_dir(self, location, layout):
        mode = yjj.get_mode_name(location.mode)
        category = yjj.get_category_name(location.category)
        p = os.path.join(self._home, category, location.group, location.name, yjj.get_layout_name(layout), mode)
        try:
            os.makedirs(p)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        return p

    def layout_file(self, location, layout, name):
        return os.path.join(self.layout_dir(location, layout), "{}.{}".format(name, yjj.get_layout_name(layout)))

    def default_to_system_db(self, location, name):
        file = os.path.join(self.layout_dir(location, yjj.layout.SQLITE), "{}.{}".format(name, yjj.get_layout_name(yjj.layout.SQLITE)))
        if os.path.exists(file):
            return file
        else:
            system_location = yjj.location(yjj.mode.LIVE, yjj.category.SYSTEM, "etc", "kungfu", self)
            system_file = os.path.join(self.layout_dir(system_location, yjj.layout.SQLITE),
                                       "{}.{}".format(name, yjj.get_layout_name(yjj.layout.SQLITE)))
            shutil.copy(system_file, file)
            return file

    def list_page_id(self, location, dest_id):
        page_ids = []
        for journal in glob.glob(os.path.join(self.layout_dir(location, yjj.layout.JOURNAL), hex(dest_id)[2:] + '.*.journal')):
            match = JOURNAL_PAGE_PATTERN.match(journal[len(self._home) + 1:])
            if match:
                page_id = match.group(6)
                page_ids.append(int(page_id))
        return page_ids

    def list_locations(self, category, group, name, mode):
        search_path = os.path.join(self._home, category, group, name, 'journal', mode)
        locations = []
        for journal in glob.glob(search_path):
            match = JOURNAL_LOCATION_PATTERN.match(journal[len(self._home) + 1:])
            if match:
                category = match.group(1)
                group = match.group(2)
                name = match.group(3)
                mode = match.group(4)
                location = yjj.location(MODES[mode], CATEGORIES[category], group, name, self)
                locations.append(location)
        return locations

    def list_location_dest(self, location):
        search_path = os.path.join(self._home, yjj.get_category_name(location.category),
                                   location.group, location.name, 'journal',
                                   yjj.get_mode_name(location.mode), '*.journal')
        readers = {}
        for journal in glob.glob(search_path):
            match = JOURNAL_PAGE_PATTERN.match(journal[len(self._home) + 1:])
            if match:
                dest = match.group(5)
                page_id = match.group(6)
                if dest in readers:
                    readers[int(dest, 16)].append(page_id)
                else:
                    readers[int(dest, 16)] = [page_id]
        return list(readers.keys())

from pathlib import Path


class DisplayablePath(object):
    display_filename_prefix_middle = '├──'
    display_filename_prefix_last = '└──'
    display_parent_prefix_middle = '    '
    display_parent_prefix_last = '│   '

    def __init__(self, path, parent_path, is_last):
        self.path = Path(str(path))
        self.parent = parent_path
        self.is_last = is_last
        self.depth = self.parent.depth + 1 if self.parent else 0

    @classmethod
    def make_tree(cls, root, parent=None, is_last=False, criteria=None):
        root = Path(str(root))
        criteria = criteria or cls._default_criteria

        displayable_root = cls(root, parent, is_last)
        yield displayable_root

        children = sorted([path for path in root.iterdir()
                                   if criteria(path)], key=lambda s: str(s).lower())
        count = 1
        for path in children:
            is_last = count == len(children)
            if path.is_dir():
                yield from cls.make_tree(path,
                                         parent=displayable_root,
                                         is_last=is_last,
                                         criteria=criteria)
            else:
                yield cls(path, displayable_root, is_last)
            count += 1

    @classmethod
    def _default_criteria(cls, path):
        return True

    @property
    def displayname(self):
        if self.path.is_dir():
            return self.path.name + '/'
        return self.path.name

    def displayable(self):
        if self.parent is None:
            return self.displayname

        _filename_prefix = (self.display_filename_prefix_last if self.is_last
                            else self.display_filename_prefix_middle)

        parts = ['{!s} {!s}'.format(_filename_prefix, self.displayname)]

        parent = self.parent
        while parent and parent.parent is not None:
            parts.append(self.display_parent_prefix_middle if parent.
                         is_last else self.display_parent_prefix_last)
            parent = parent.parent

        return ''.join(reversed(parts))


def get_output_tree(path_to_draw):
    from pathlib import Path
    chain_log = "=" * 79 + "\n"
    chain_log += " " * 30 + "Output Directories" + " " * 31 + "\n"
    chain_log += "=" * 79 + "\n"
    # the call of Path ensure the path is valid ?
    out_cont = DisplayablePath.make_tree(Path(path_to_draw))
    for path in out_cont:
        chain_log += path.displayable() + "\n"
    return chain_log + "\n" * 3


def get_locale(path):
    import os
    tempfile = os.path.join(path, "locale.txt")
    os.system("locale>{}".format(tempfile))
    chain_log = "=" * 79 + "\n"
    chain_log += " " * 36 + "LOCALE" + " " * 37 + "\n"
    chain_log += "=" * 79 + "\n"
    with open(tempfile, 'r') as f_tmp:
        chain_log += f_tmp.read()
    os.remove(tempfile)
    return chain_log + "\n" * 3


def get_package_version(path):
    import os
    tempfile = os.path.join(path, "package.txt")
    os.system("conda list>{}".format(tempfile))
    chain_log = "=" * 79 + "\n"
    chain_log += " " * 30 + "Environment package" + " " * 30 + "\n"
    chain_log += "=" * 79 + "\n"
    with open(tempfile, 'r') as f_tmp:
        chain_log += f_tmp.read()
    os.remove(tempfile)
    return chain_log + "\n" * 3


def get_config_file(configfile):
    chain_log = "=" * 79 + "\n"
    chain_log += " " * 30 + "Configuration file" + " " * 30 + "\n"
    chain_log += "=" * 79 + "\n"
    with open(configfile, 'r') as f_tmp:
        chain_log += f_tmp.read()
    return chain_log + "\n" * 3


def get_cont_path_from_config(configfile):
    import os
    from iota2.Common import ServiceConfigFile as SCF
    cfg = SCF.serviceConfigFile(configfile)
    block_chain = cfg.getSection("chain")
    glob_str = ""
    for key in block_chain.keys():
        if 'path' in key.lower():
            path_to_draw = cfg.getParam("chain", key)
            if isinstance(path_to_draw, str) and os.path.isdir(path_to_draw):
                chain_log = "=" * 79 + "\n"
                chain_log += " " * int(
                    (79 - len(key)) / 2) + "{}".format(key)
                chain_log += " " * int((79 - len(key)) / 2) + "\n"
                chain_log += "=" * 79 + "\n"
                out_cont = DisplayablePath.make_tree(Path(path_to_draw))
                for path in out_cont:
                    chain_log += path.displayable() + "\n"
                glob_str += chain_log + "\n" * 3
    return glob_str


def get_cont_file_from_config(configfile):
    import os
    from iota2.Common import ServiceConfigFile as SCF
    cfg = SCF.serviceConfigFile(configfile)
    block_chain = cfg.getSection("chain")
    glob_str = ""
    for key in block_chain.keys():
        file_to_read = cfg.getParam("chain", key)
        if isinstance(file_to_read, str) and (
            os.path.isfile(file_to_read)
            and ('txt' in file_to_read or 'csv' in file_to_read)
        ):
            chain_log = "=" * 79 + "\n"
            chain_log += " " * int((79 - len(key)) / 2) + "{}".format(key)
            chain_log += " " * int((79 - len(key)) / 2) + "\n"
            chain_log += "=" * 79 + "\n"
            cont = "Unable to read file" + file_to_read
            with open(file_to_read, "r") as contfile:
                cont = contfile.read()
            chain_log += cont
            glob_str += chain_log + "\n" * 3
    return glob_str


def get_log_file(logfile):
    import os
    chain_log = "=" * 79 + "\n"
    name = os.path.basename(logfile)
    chain_log += " " * int((79 - len(name)) / 2) + "{}".format(name)
    chain_log += " " * int((79 - len(name)) / 2) + "\n"
    chain_log += "=" * 79 + "\n"
    cont = "Unable to open logfile : " + logfile
    with open(logfile, "r") as logf:
        cont = logf.read()
    chain_log += cont
    return chain_log + "\n" * 3


def get_log_info(path, configfile, logfile):
    chain = "\n"
    chain += get_config_file(configfile)
    chain += get_log_file(logfile)
    chain += get_cont_path_from_config(configfile)
    chain += get_cont_file_from_config(configfile)
    chain += get_locale(path)
    chain += get_package_version(path)
    return chain

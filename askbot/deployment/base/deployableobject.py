import os.path
import shutil

from askbot.deployment.base.template_loader import DeploymentTemplate
from askbot.deployment.base.exceptions import AskbotDeploymentError
from askbot.deployment.base import ObjectWithOutput

class DeployableObject(ObjectWithOutput):
    """Base class for filesystem objects, i.e. files and directories, that can
    be/are deployed using askbot-setup."""
    def __init__(self, name, src_path=None, dst_path=None):
        super(DeployableObject, self).__init__(verbosity=2)
        self.name = name
        self._src_path = src_path
        self._dst_path = dst_path

    @property
    def src_path(self):
        return self._src_path

    @src_path.setter
    def src_path(self, value):
        self._src_path = value

    @property
    def dst_path(self):
        return self._dst_path

    @dst_path.setter
    def dst_path(self, value):
        self._dst_path = value

    @property
    def src(self):
        return os.path.join(self.src_path, self.name)

    @property
    def dst(self):
        return os.path.join(self.dst_path, self.name)

    def _deploy_now(self):
        """virtual protected"""

    def deploy(self):
        """The main method of this class. DeployableComponents call this method
         to have this object do the filesystem operations which deploys
         whatever this class represents."""
        self.print(f'*    {self.dst} from {self.src}')
        try:
            self._deploy_now()
        except AskbotDeploymentError as e:
            self.print(e)

class DeployableFile(DeployableObject):
    """This class collects all logic w.r.t. a single files. It has to be
    subclassed and the subclasses must/should overwrite _deploy_now to call
    one of the methods defined in this class. At the time of this writing, this
    is either _render_with_jinja2 or _copy.

    The subclasses may then be used to deploy a single file.
    """
    def __init__(self, name, src_path=None, dst_path=None):
        super(DeployableFile, self).__init__(name, src_path, dst_path)
        self.context = dict()
        self.skip_silently = list()
        self.forced_overwrite = list()

    # the different approaches for force and skip feel a little odd.
    def __validate(self):
        matches = [self.dst for c in self.forced_overwrite
                   if self.dst.endswith(f'{os.path.sep}{c}')]
        exists = os.path.exists(self.dst)
        force  = len(matches) > 0
        skip   = self.dst.split(os.path.sep)[-1] in self.skip_silently
        return exists, force, skip

    def _render_with_jinja2(self, context):
        exists, force, skip = self.__validate()
        if exists:
            raise AskbotDeploymentError(f'     You already have a file "{self.dst}" please merge the contents.')
        template = DeploymentTemplate('dummy.name')  # we use this a little differently than originally intended
        template.tmpl_path = self.src
        content = template.render(context) # do not put this in the context. If this statement fails, we do not want an empty self.dst to be created!
        with open(self.dst, 'w+') as output_file:
            output_file.write(content)

    def _copy(self):
        exists, force, skip = self.__validate()
        if exists:
            if skip: # this makes skip more important than force. This is good, because when in doubt, we rather leave the current installation the way it is. This is bad because we cannot explicitly force an overwrite.
                return
            elif force:
                self.print('     ^^^ forced overwrite!')
            else:
                raise AskbotDeploymentError(f'     You already have a file "{self.dst}", please add contents of {self.src}.')
        shutil.copy(self.src, self.dst)

    #####################
    ## from path_utils ##
    #####################
    def _touch(self, times=None):
        """implementation of unix ``touch`` in python"""
        #http://stackoverflow.com/questions/1158076/implement-touch-using-python
        try:
            os.utime(self.dst, times)
        except:
            open(self.dst, 'a').close()


class DeployableDir(DeployableObject):
    def __init__(self, name, parent=None, *content):
        super(DeployableDir, self).__init__(name)
        self.content = list(content)
        if parent is not None:
            self.dst_path = self.__clean_directory(parent)

    @DeployableObject.verbosity.setter
    def verbosity(self, value):
        self._verbosity = value
        for child in self.content:
            child.verbosity = value

    @DeployableObject.src_path.setter
    def src_path(self, value):
        value = self.__clean_directory(value)
        self._src_path = value
        for child in self.content:
            child.src_path = value

    @DeployableObject.dst_path.setter
    def dst_path(self, value):
        value = self.__clean_directory(value)
        self._dst_path = value
        for child in self.content:
            child.dst_path = self.dst

    @property
    def context(self):
        raise AttributeError(f'{self.__class__} does not store context information')

    @property
    def skip_silently(self):
        raise AttributeError(f'{self.__class__} does not store file skip information')

    @property
    def forced_overwrite(self):
        raise AttributeError(f'{self.__class__} does not store file overwrite information')

    # maybe deepcopy() in the following three setters. maybe there's an advantage in not deepcopy()ing here. time will tell.
    @context.setter
    def context(self, value):
        for child in self.content: # in theory, we only want this for directories and rendered files.
            child.context = value

    @skip_silently.setter
    def skip_silently(self, value):
        for child in self.content: # in practice, we only need this for directories and copied files.
            child.skip_silently = value

    @forced_overwrite.setter
    def forced_overwrite(self, value):
        for child in self.content: # in practice, we only need this for directories and copied files.
            child.forced_overwrite = value

    def _link_dir(self):
        """Derived from __create_path()"""
        if os.path.isdir(self.dst):
            return
        elif os.path.exists(self.dst):
            raise AskbotDeploymentError('expect directory or a non-existing path')
        else:
            os.symlink(self.src, self.dst)

    #####################
    ## from path_utils ##
    #####################
    def __create_path(self):
        """equivalent to mkdir -p"""
        if os.path.isdir(self.dst):
            return
        elif os.path.exists(self.dst):
            raise AskbotDeploymentError('expect directory or a non-existing path')
        else:
            os.makedirs(self.dst)

    @staticmethod
    def __clean_directory(directory):
        """Returns normalized absolute path to the directory
        regardless of whether it exists or not
        or ``None`` - if the path is a file or if ``directory``
        parameter is ``None``"""
        if directory is None:
            return None

        directory = os.path.normpath(directory)
        directory = os.path.abspath(directory)

        #if os.path.isfile(directory):
        #    print(messages.CANT_INSTALL_INTO_FILE % {'path': directory})
        #    return None
        return directory

    def _deploy_now(self):
        self.__create_path()

    def deploy(self):
        self._deploy_now() # we don't try-except this, b/c input validation is supposed to identify problems before this code runs. If an exception is raised here, it's an issue that must be handled elsewhere.
        for node in self.content:
            node.deploy()

from .objectwithoutput import ObjectWithOutput

class ConfigManager(ObjectWithOutput):
    """ConfigManagers are used to ensure the installation can proceed.

    Each ConfigManager looks at some installation parameters, usually
    grouped by the aspect of Askbot they configure. For instance there is
    a ConfigManager for the database backend and another one for the cache
    backend. The task of a ConfigManager is to ensure that the combination
    of install parameters it analyses is sensible for an Askbot installation.

    The installer calls a ConfigManager's complete() method and passes it
    its entire collection of installation parameters, a dictionary.
    A ConfigManager only looks at those installation parameters which have
    been register()-ed with the ConfigManager.

    For each installation parameter there is registered class, derived from
    ConfigField, which can determine if a parameter's value is acceptable and
    ask the user to provide a value for the parameter.

    The ConfigManager knows in which order to process its registered
    installation parameters and contains all the logic determining if a user
    should be asked for a(nother) value. It also remembers all values it
    accepts and in the process may also modify the behaviour of the
    ConfigField classes, to fit with the previously accepted values. For
    instance, usually the DbConfigManager insists on credentials for accessing
    the database, but if a user selects SQLite as database backend, the
    DbConfigManager will *NOT* insist on credentials for accessing the
    database, because SQLite does not need authentication.
    """
    strings = {
        'eNoValue': 'You must specify a value for "{name}"!',
    }

    def __init__(self, interactive=True, verbosity=1, force=False):
        self._interactive = interactive
        self._catalog = dict() # we use this to hold the ConfigFields
        self.keys = set() # we use this for scoping and consistency
        self._ordered_keys = list() # we use this for ordering our keys
        self._managed_config = dict() # we use this as regestry for completed work
        super(ConfigManager, self).__init__(verbosity=verbosity, force=force)
        self.interactive = interactive

    @property
    def interactive(self):
        return self._interactive

    @interactive.setter
    def interactive(self, interactive):
        self._interactive = interactive
        for name, handler in self._catalog.items():
            if hasattr(handler,'interactive'):
                handler.interactive = interactive

    @property
    def force(self):
        return self._force

    @force.setter
    def force(self, force):
        self._force = force
        for name, handler in self._catalog.items():
            if hasattr(handler,'force'):
                handler.force = force

    @ObjectWithOutput.verbosity.setter
    def verbosity(self, verbosity):
        self._verbosity = verbosity
        for name, handler in self._catalog.items():
            if hasattr(handler, 'verbosity'):
                handler.verbosity = verbosity

    def register(self, name, handler):
        """Add the ability to handle a specific install parameter.
        Parameters:
        - name: the install parameter to handle
        - handler: the class to handle the parameter"""
        handler.verbosity = self.verbosity
        self._catalog[name] = handler
        self.keys.update({name})
        self._ordered_keys.append(name)


    def configField(self, name):
        if name not in self.keys:
            raise KeyError(f'{self.__class__.__name__}: No handler for {name} registered.')
        return self._catalog[name]

    def _remember(self, name, value):
        """With this method, instances remember the accepted piece of
        information for a given name. Making this a method allows derived
        classes to perform additional work on accepting a piece of
        information."""
        self._managed_config.setdefault(name, value)

    def _complete(self, name, current_value):
        """The generic procedure to ensure an installation parameter is
        sensible and bug the user until a sensible value is provided.

        If this is not an interactive installation, a not acceptable() value
        raises a ValueError"""
        if name not in self.keys:
            raise KeyError

        configField   = self._catalog[name]

        while not configField.acceptable(current_value):
            self.print(f'Current value {current_value} not acceptable!', 2)
            if not self.interactive:
                raise ValueError(self.strings['eNoValue'].format(name=name))
            current_value = configField.ask_user(current_value)

        # remember the piece of information we just determined acceptable()
        self._remember(name, current_value)
        return current_value

    def _order(self, keys):
        """Gives implementations control over the order in which they process
        installation parameters. A ConfigManager should restrict itself to
        the ConfigFields it knows about and ensure each field is only
        consulted once."""
        ordered_keys = []
        known_fields = list(self.keys & set(keys)) # only handle keys we know
        for f in self._ordered_keys: # use this order
            if f in known_fields: # only fields the caller wants sorted
                ordered_keys.append(f)
                known_fields.remove(f) # avoid duplicates
        return ordered_keys

    def complete(self, collection):
        """Main method of this :class:ConfigManager.
        Consumers use this method to ensure their data in :dict:collection is
        sensible for installing Askbot.
        """
        contribution = dict()
        keys = self.keys & set(collection.keys()) # scope to this instance
        for k in self._order(keys):
            v = self._complete(k, collection[k])
            contribution.setdefault(k, v)
        collection.update(contribution)

    def reset(self):
        """ConfigManagers may keep a state. This method shall be used to reset
        the state to whatever that means for the specific config manager. This
        implementation merely flushes the memory about completed work."""
        self._managed_config = dict()



# one could make a case for not deriving ConfigManagerCollection from
# ConfigManager because the collection serves a different purpose than the
# individual manager, but they are still quite similar
class ConfigManagerCollection(ConfigManager):
    """
    Container class for ConfigManagers.
    """
    def __init__(self, interactive=False, verbosity=1):
        super(ConfigManagerCollection, self).__init__(interactive=interactive, verbosity=verbosity)

    def configManager(self, name):
        return super(ConfigManagerCollection, self).configField(name)

    def complete(self, *args, **kwargs):
        for manager in self._order(self.keys):
            handler = self.configManager(manager)
            handler.complete(*args, **kwargs)

    # these should never be called. we keep these implementations, just in case
    def _remember(self, name, value):
        raise NotImplementedError(f'Not implemented in {self.__class__.__name__}.')

    def _complete(self, name, value):
        raise NotImplementedError(f'Not implemented in {self.__class__.__name__}.')

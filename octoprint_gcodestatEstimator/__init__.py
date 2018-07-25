# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin

import re

from octoprint.printer.estimation import PrintTimeEstimator


class GcodestatPrintTimeEstimator(PrintTimeEstimator):
    def __init__(self, job_type):
        PrintTimeEstimator.__init__(self, job_type)
        self._job_type = job_type
        self.estimated_time = 0
        self.percentage_done = -1

    def estimate(self, *args, **kwargs):
        if self._job_type != "local" or self.percentage_done == -1:
            return PrintTimeEstimator.estimate(self, *args, **kwargs)
        return self.estimated_time, "estimate"

class GcodestatPrintTimeEstimatorPlugin(octoprint.plugin.StartupPlugin):

    pw = re.compile('M73 P([0-9]+) R([0-9]+)')

    def __init__(self):
        self._estimator = None

    def on_after_startup(self):
        self._logger.info("Started up gcodestatEstimator")


    ##~~ queuing gcode hook

    def updateEstimation(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
        if gcode != "M73" or self._estimator is None:
            return

        self._logger.debug("gcodestatEstimator: M73 found")

        mw = self.pw.match(cmd)
        if mw:
            self._estimator.estimated_time = float(mw.group(2))*60 
            self._estimator.percentage_done = float(mw.group(1))
        else :
            self._logger.debug("gcodestatEstimator: NO MATCH!")
            return

        self._logger.debug("gcodestatEstimator: {}% {}sec".format(self._estimator.percentage_done, self._estimator.estimated_time))

    ##~~ estimator factory hook

    def estimator_factory(self):
        def factory(*args, **kwargs):
            self._estimator = GcodestatPrintTimeEstimator(*args, **kwargs)
            return self._estimator
        return factory

    ##~~ software update hook

    def get_update_information(self):
        return dict(
            gcodestatEstimator=dict(
                displayName=self._plugin_name,
                displayVersion=self._plugin_version,

                # version check: github repository
                type="github_release",
                user="arhi",
                repo="OctoPrint-gcodestatEstimator",
                current=self._plugin_version,

                # update method: pip
                pip="https://github.com/arhi/OctoPrint-gcodestatEstimator/archive/{target_version}.zip"
            )
        )


__plugin_implementation__ = GcodestatPrintTimeEstimatorPlugin()
__plugin_hooks__ = {
    "octoprint.comm.protocol.gcode.queuing": __plugin_implementation__.updateEstimation,
    "octoprint.printer.estimation.factory": __plugin_implementation__.estimator_factory,
    "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
}

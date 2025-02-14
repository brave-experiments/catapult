# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Provide a TestCase base class for PageTest subclasses' unittests."""

import unittest

from telemetry import story
from telemetry.core import util
from telemetry.internal.results import results_options
from telemetry.internal import story_runner
from telemetry.page import page as page_module
from telemetry.page import legacy_page_test


BENCHMARK_NAME = 'page_test_test_case.RunMeasurement'


class BasicTestPage(page_module.Page):
  def __init__(self, url, story_set, base_dir, name=''):
    super(BasicTestPage, self).__init__(url, story_set, base_dir, name=name)

  def RunPageInteractions(self, action_runner):
    with action_runner.CreateGestureInteraction('ScrollAction'):
      action_runner.ScrollPage()
    # Undo the above action so that we can run BasicTestPage again if we need
    # to, without closing the browser. Otherwise, tests may see unexpected
    # behaviour on Chrome OS; see crbug.com/851523 for an example.
    action_runner.ScrollPage(direction='up')


class PageTestTestCase(unittest.TestCase):
  """A base class to simplify writing unit tests for PageTest subclasses."""

  def CreateStorySetFromFileInUnittestDataDir(self, test_filename):
    ps = self.CreateEmptyPageSet()
    page = BasicTestPage('file://' + test_filename, ps, base_dir=ps.base_dir,
                         name=test_filename)
    ps.AddStory(page)
    return ps

  def CreateEmptyPageSet(self):
    base_dir = util.GetUnittestDataDir()
    ps = story.StorySet(base_dir=base_dir)
    return ps

  def RunMeasurement(self, measurement, ps, options=None, run_options=None):
    """Runs a measurement against a story set, returning a results object.

    Args:
      measurement: A test object: either a story_test.StoryTest or
        legacy_page_test.LegacyPageTest instance.
      ps: A story set.
      options: (DEPRECATED) An object with basic browser options, e.g. as
        returned by options_for_unittests.GetCopy().
        TODO(crbug.com/985712): Remove when no longer used by RunMeasurement
        clients in tools/perf of chromium repository.
      run_options: An object with all options needed to run stories; can be
        created with the help of options_for_unittests.GetRunOptions().
    """
    if run_options is None:
      assert options, 'Either options or run_options should be specified.'
      temp_parser = options.CreateParser()
      story_runner.AddCommandLineArgs(temp_parser)
      defaults = temp_parser.get_default_values()
      for k, v in defaults.__dict__.items():
        if hasattr(options, k):
          continue
        setattr(options, k, v)
      story_runner.ProcessCommandLineArgs(temp_parser, options)
      options.output_formats = ['none']
      options.output_file = None
      run_options = options
    else:
      assert options is None, 'Should not specify both options and run_options.'

    if isinstance(measurement, legacy_page_test.LegacyPageTest):
      measurement.CustomizeBrowserOptions(run_options.browser_options)
    results = results_options.CreateResults(
        run_options, benchmark_name=BENCHMARK_NAME)
    story_runner.Run(measurement, ps, run_options, results)
    return results

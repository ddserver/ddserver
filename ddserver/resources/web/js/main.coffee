###
Copyright 2014 Sven Reissmann <sven@0x80.io>

This file is part of ddserver. It is licensed under the terms of the GNU
Affero General Public License version 3. See <http://www.gnu.org/licenses/>.
###

require.config
  urlArgs: 'v=' + new Date()
  baseUrl: '/static/js'
  paths:
    jquery: 'lib/jquery.min'
    knockout: 'lib/knockout'
    pager: 'lib/pager.min'
    bootstrap: 'lib/bootstrap.min'
    pwstrength: 'lib/pwstrength'
    chart: 'chart.min'
    text: 'text'
    vars: 'vars'


@requireVM = (module) ->
  (callback) ->
    require ["/pages/#{module}/model.js"], (vm) ->
      callback new vm


@requireHTML = (module) ->
  (page, callback) ->
    require ["text!/pages/#{module}/view.html"], (html) ->
      $(page.element).html html
      callback()


require ['jquery', 'knockout', 'pager', 'bootstrap'], ($, ko, pager) ->
  class VM
    constructor: ->
      @ui_displayMainMenu = ko.computed =>
        @username() != ""
        
      @username = ko.observable ""

    # check whether the current user is logged in or not
    # redirect to login page, if not logged in
    isLoggedIn: (page, route, callback) =>
      $.ajax
        url: '/_auth/getlogin'
        dataType: 'json'
        success: (result) =>
          if result.success == true
            @username result.username
            callback()
          else
            window.location.href = "/#system/login"
        error: (jqXHR, status, error) =>
          @error error
          window.location.href = "/#system/login"

    # logout
    logout: ->
      $.ajax
        url: '/_auth/logout'
        dataType: 'json'
        success: (result) =>
          window.location.href = "/"


  vm = new VM
  pager.extendWithPage vm
  ko.applyBindings vm


  pager.onBindingError.add( 
    (event) ->
      page = event.page
      $(page.element).empty().append('<div class="text-danger"> Error Loading Page</div>')
  )

  pager.start()

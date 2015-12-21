(function(window, angular, undefined) {

  'use strict';

  var clubadm = angular.module('clubadm', [
    'ui.router',
    'angularMoment',
    'luegg.directives',
    'clubadm.controllers',
    'clubadm.services',
  ]);

  clubadm.run([
    '$rootScope', '$state', 'amMoment', 'UserService',
    function($rootScope, $state, amMoment, UserService) {
      $rootScope.$state = $state;
      $rootScope.user = UserService.getCurrentUser();

      amMoment.changeLocale('ru');
    }]);

  clubadm.config([
    '$httpProvider', '$stateProvider', '$urlRouterProvider',
    function($httpProvider, $stateProvider, $urlRouterProvider) {
      var token = window.jsdata.security.token;
      $httpProvider.defaults.headers.common['X-CSRFToken'] = token;

      $stateProvider.state('home', {
        url: '/',
        controller: 'HomeController',
      });

      $stateProvider.state('season', {
        abstract: true,
        url: '/{year:[0-9]{4}}',
        templateUrl: window.jsdata.partials.season,
        controller: 'SeasonController',
      });

      $stateProvider.state('season.welcome', {
        url: '',
        templateUrl: window.jsdata.partials.welcome,
        controller: 'WelcomeController',
        data: {
          classname: 'welcome',
        },
      });

      $stateProvider.state('season.profile', {
        url: '/profile',
        templateUrl: window.jsdata.partials.profile,
        controller: 'ProfileController',
        data: {
          classname: 'profile',
        },
      });

      $urlRouterProvider.otherwise('/');
    }]);

})(window, window.angular);

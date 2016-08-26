var outbitApp = angular.module('outbitApp', [ 'ngRoute', 'outbitControllers']);

outbitApp.config(['$routeProvider',
  function($routeProvider) {
      $routeProvider.
        when('/login', {
         templateUrl: 'templates/login.html',
         controller: 'outbitCtrl'
        }).
        when('/jobs', {
         templateUrl: 'templates/jobs.html',
         controller: 'outbitCtrl'
        }).
        when('/actions', {
         templateUrl: 'templates/actions.html',
         controller: 'outbitCtrl'
        }).
        when('/user', {
         templateUrl: 'templates/user.html',
         controller: 'outbitCtrl'
        }).
        otherwise( {
         templateUrl: 'templates/login.html',
         controller: 'dwCtrl'
        });
  }]);
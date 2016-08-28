var outbitApp = angular.module('outbitApp', [ 'ngRoute', 'outbitControllers', 'satellizer']);

outbitApp.config(['$routeProvider', '$httpProvider', '$authProvider',
  function($routeProvider, $httpProvider, $authProvider) {
    // Login Required
    function loginRequired($q, $location, $auth, $route) {
        var deferred = $q.defer();
        if ($auth.isAuthenticated()) {
            deferred.resolve();
        } else {
            $location.path('http://127.0.0.1:8088/login');
        }
        return deferred.promise;
    }

      // Login URL
      $authProvider.loginUrl = 'http://127.0.0.1:8088/login';

      // Support Cross-Domain
      $httpProvider.defaults.useXDomain = true;
      delete $httpProvider.defaults.headers.common["X-Requested-With"];

      // Routes
      $routeProvider.
        when('/login', {
         templateUrl: 'templates/login.html',
         controller: 'outbitCtrl'
        }).
        when('/jobs', {
         templateUrl: 'templates/jobs.html',
         controller: 'outbitCtrl',
         resolve: {
            loginRequired: loginRequired
         }
        }).
        when('/actions', {
         templateUrl: 'templates/actions.html',
         controller: 'outbitCtrl',
         resolve: {
            loginRequired: loginRequired
         }
        }).
        when('/user', {
         templateUrl: 'templates/user.html',
         controller: 'outbitCtrl',
         resolve: {
            loginRequired: loginRequired
         }
        }).
        otherwise( {
         templateUrl: 'templates/login.html',
         controller: 'outbitCtrl',
         resolve: {
            loginRequired: loginRequired
         }
        });
  }]);
var bandicootControllers = angular.module('bandicootControllers', []);

bandicootControllers.controller('bandicootLoginCtrl', ['$auth', '$scope', '$http', 'toaster',
  function ($auth, $scope, $http, toaster) {
    $scope.login = function() {
      credentials = {
            username: $scope.username,
            password: $scope.password,
      }

      $auth.login(credentials).then(function(data) {
        console.log(data)
      })
      .catch(function(response){ // If login is unsuccessful, display relevant error message.
               toaster.pop({
                type: 'error',
                title: 'Login Error',
                body: response.data,
                showCloseButton: true,
                timeout: 0
                });
       });
    }
  }
]);
 
bandicootControllers.controller('bandicootNavCtrl', function($auth,  $scope) {
    // Nav only for auth users
    $scope.isAuthenticated = function() {
      return $auth.isAuthenticated();
    };
});

bandicootControllers.controller('bandicootLogoutCtrl', ["$auth", "$location", "toaster",
  function($auth, $location, toaster) { // Logout the user if they are authenticated.
    if (!$auth.isAuthenticated()) { return; }
     $auth.logout()
      .then(function() {
        toaster.pop({
                type: 'success',
                body: 'Logging out',
                showCloseButton: true,
                });
        $location.url('/login');
        });
  }
 ]); 

bandicootControllers.controller('bandicootJobsCtrl', ['$auth', '$scope', '$http', '$rootScope', "toaster",
  function ($auth, $scope, $http, $rootScope, toaster) {
      $scope.statusJob = function(jobid) {
          bandicootdata = {"action": "status", "category": "/jobs", "options": {"id": String(jobid)}};
          $http.post(document.location.protocol + '//' + $rootScope.bandicootapi_ip + ':' + $rootScope.bandicootapi_port + '/api', bandicootdata).success(function (data) {
            toaster.pop({
                type: 'success',
                body: data.response.replace(/(?:\r\n|\r|\n)/g, '<br/>'),
                showCloseButton: true,
                bodyOutputType: 'trustedHtml',
                }); 
          }).error(function (data) {
            console.log(bandicootdata);
            console.log(data);
          });
      };

      bandicootdata = {"action": "list", "category": "/jobs", "options": null};
      $http.post(document.location.protocol + '//' + $rootScope.bandicootapi_ip + ':' + $rootScope.bandicootapi_port + '/api', bandicootdata).success(function (data) {
        $scope.jobs = data.api_response;
      }).error(function (data) {
        console.log(data);
      });
  }
]);

bandicootControllers.controller('bandicootActionsCtrl', ['$auth', '$scope', '$http', '$rootScope', '$location',
  function ($auth, $scope, $http, $rootScope, $location) {
      $scope.builtinActionsFilter = function(element) {
        var category_filter = element.category.match(/^actions$|^users$|^roles$|^secrets$|^plugins$|^jobs$|^schedules$|^inventory$/) ? false : true;
        var action_filter = element.action.match(/^ping$|^logs$|^help$/) ? false : true;
        return action_filter && category_filter;
      };

      $scope.runJob = function(category, action, options=null) {
          bandicootdata = {"action": action, "category": "/"+category, "options": options}
          $http.post(document.location.protocol + '//' + $rootScope.bandicootapi_ip + ':' + $rootScope.bandicootapi_port + '/api', bandicootdata).success(function (data) {
            $location.url('/jobs');
          }).error(function (data) {
            console.log(bandicootdata);
            console.log(data);
          });
      };

      bandicootdata = {"action": "help", "category": "/", "options": null}
      $http.post(document.location.protocol + '//' + $rootScope.bandicootapi_ip + ':' + $rootScope.bandicootapi_port + '/api', bandicootdata).success(function (data) {
        $scope.actions = data.api_response
      }).error(function (data) {
        console.log(data);
      });
  }
]);

bandicootControllers.controller('bandicootUserCtrl', ['$auth', '$scope', '$http', '$rootScope',
  function ($auth, $scope, $http, $rootScope) {
      bandicootdata = {"action": "list", "category": "/users", "options": null}
      $http.post(document.location.protocol + '//' + $rootScope.bandicootapi_ip + ':' + $rootScope.bandicootapi_port + '/api', bandicootdata).success(function (data) {
        $scope.users = data.response.split("\n");
      }).error(function (data) {
        console.log(data);
      });
  }
]);
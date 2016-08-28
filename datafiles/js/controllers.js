var outbitControllers = angular.module('outbitControllers', []);

outbitControllers.controller('outbitLoginCtrl', ['$auth', '$scope', '$http', 'toaster',
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
 
outbitControllers.controller('outbitNavCtrl', function($auth,  $scope) {
    // Nav only for auth users
    $scope.isAuthenticated = function() {
      return $auth.isAuthenticated();
    };
});

outbitControllers.controller('outbitLogoutCtrl', ["$auth", "$location", "toaster",
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

outbitControllers.controller('outbitJobsCtrl', ['$auth', '$scope', '$http',
  function ($auth, $scope, $http) {
      outbitdata = {"action": "list", "category": "/jobs", "options": null}
      $http.post('http://127.0.0.1:8088/api', outbitdata).success(function (data) {
        $scope.jobs = data.response.split("\n");
      }).error(function (data) {
        console.log(data);
      });
  }
]);

outbitControllers.controller('outbitActionsCtrl', ['$auth', '$scope', '$http',
  function ($auth, $scope, $http) {
      outbitdata = {"action": "help", "category": "/", "options": null}
      $http.post('http://127.0.0.1:8088/api', outbitdata).success(function (data) {
        $scope.actions = data.response.split("\n");
      }).error(function (data) {
        console.log(data);
      });
  }
]);

outbitControllers.controller('outbitUserCtrl', ['$auth', '$scope', '$http',
  function ($auth, $scope, $http) {
      outbitdata = {"action": "list", "category": "/users", "options": null}
      $http.post('http://127.0.0.1:8088/api', outbitdata).success(function (data) {
        $scope.users = data.response.split("\n");
      }).error(function (data) {
        console.log(data);
      });
  }
]);
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

outbitControllers.controller('outbitJobsCtrl', ['$auth', '$scope', '$http',
  function ($auth, $scope, $http) {
      outbitdata = {"action": "list", "category": "/users", "options": null}
      $http.post('http://127.0.0.1:8088/api', outbitdata).success(function (data) {
        console.log("result: " + data.response);
      }).error(function (data) {
        console.log(data);
      });
  }
]);
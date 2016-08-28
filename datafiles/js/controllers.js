var outbitControllers = angular.module('outbitControllers', []);

outbitControllers.controller('outbitLoginCtrl', ['$auth', '$scope', '$http',
  function ($auth, $scope, $http) {
      credentials = {
            username: "superadmin",
            password: "password",
      }

      $auth.login(credentials).then(function(data) {
        console.log(data)
      });
      console.log("login")
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
(function(window, angular) {

    "use strict";

    var clubadm = angular.module("clubadm", ["angularMoment", "luegg.directives"]);

    clubadm.run(["$rootScope", "amMoment", function($rootScope, amMoment) {
        amMoment.changeLocale("ru");
    }]);

    clubadm.config(["$httpProvider", function($httpProvider) {
        $httpProvider.defaults.headers.common["X-CSRFToken"] = window.csrf_token;
    }]);

    clubadm.controller("ProfileController", ["$scope", "$http", function($scope, $http) {
        var lastUpdate = 0;
        $scope.chat = {};

        function update(data) {
            lastUpdate = Math.floor(Date.now() / 1000);
            $scope.season = data.season;
            $scope.member = data.member;

            if (data.user) {
                $scope.user = data.user;
            }

            if (data.member) {
                $scope.form = angular.copy(data.member);
            } else {
                $scope.form = {};
            }
        }

        function readMails(year, sender, timestamp) {
            $http({
                url: "/" + year + "/read_mails/",
                method: "POST",
                data: "sender=" + sender + "&timestamp=" + timestamp,
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            }).then(function(response) {
                update(response.data);
            }, function(response) {
                alert(response.data.error);
            });
        }

        $scope.$watch("flippers.santa", function(newValue, oldValue) {
            if (oldValue == false && newValue == true) {
                readMails($scope.season.year, "santa", lastUpdate);
            }
        });

        $scope.$watch("flippers.giftee", function(newValue, oldValue) {
            if (oldValue == false && newValue == true) {
                readMails($scope.season.year, "giftee", lastUpdate);
            }
        });

        $scope.signUp = function() {
            var data = [
                "fullname=", encodeURIComponent($scope.form.fullname),
                "&postcode=", encodeURIComponent($scope.form.postcode),
                "&address=", encodeURIComponent($scope.form.address),
            ];

            $http({
                url: "/" + $scope.season.year + "/signup/",
                method: "POST",
                data: data.join(""),
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            }).then(function(response) {
                update(response.data);
            }, function(response) {
                alert(response.data.error);
            });
        };

        $scope.signOut = function() {
            var url = "/" + $scope.season.year + "/signout/";
            $http.post(url).then(function(response) {
                update(response.data);
            }, function(response) {
                alert(response.data.error);
            });
        };

        $scope.sendGift = function() {
            var url = "/" + $scope.season.year + "/send_gift/";
            $http.post(url).then(function(response) {
                update(response.data);
            }, function(response) {
                alert(response.data.error);
            });
        };

        $scope.receiveGift = function() {
            var url = "/" + $scope.season.year + "/receive_gift/";
            $http.post(url).then(function(response) {
                update(response.data);
            }, function(response) {
                alert(response.data.error);
            });
        };

        $scope.sendMail = function(recipient) {
            if (recipient == "giftee") {
                var message = $scope.chat.giftee_message;
                $scope.chat.giftee_message = "";
            } else {
                var message = $scope.chat.santa_message;
                $scope.chat.santa_message = "";
            }
            $http({
                url: "/" + $scope.season.year + "/send_mail/",
                method: "POST",
                data: "recipient=" + recipient + "&body=" + encodeURIComponent(message),
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            }).then(function(response) {
                update(response.data);
            }, function(response) {
                alert(response.data.error);
            });
        };

        update(window.prefetched);
    }]);

})(window, window.angular);

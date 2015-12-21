(function(window, angular, undefined) {

  'use strict';

  var controllers = angular.module('clubadm.controllers', []);

  /**
   * Контроллер главной страницы. Перенаправляет пользователя на последний
   * доступный сезон.
   */
  controllers.controller('HomeController', [
    '$state', 'SeasonService',
    function($state, SeasonService) {
      SeasonService.getLatest().then(function(response) {
        $state.go('season.welcome', {
          year: response.data.year
        });
      });
    }]);

  /**
   * Промежуточный контроллер, который загружает информацию о сезоне.
   */
  controllers.controller('SeasonController', [
    '$scope', '$state', '$stateParams', 'SeasonService',
    function($scope, $state, $stateParams, SeasonService) {
      SeasonService.getByYear($stateParams.year).then(function(response) {
        $scope.season = response.data;
      }, function(response) {
        $state.go('home');
      });
    }]);

  /**
   * Контроллер страницы с предложением принять участие в акции.
   */
  controllers.controller('WelcomeController', [
    '$state', '$stateParams', 'UserService',
    function($state, $stateParams, UserService) {
      if (UserService.isUserLoggedIn()) {
        $state.go('season.profile', $stateParams);
      }
    }]);

  /**
   * Контроллер личной страницы участника.
   */
  controllers.controller('ProfileController', [
    '$scope', '$state', '$stateParams', 'UserService', 'SeasonService',
    function($scope, $state, $stateParams, UserService, SeasonService) {
      if (!UserService.isUserLoggedIn()) {
        $state.go('season.welcome', $stateParams);
      }

      SeasonService.getMemberByYear($stateParams.year).then(function(response) {
        $scope.member = response.data;
        $scope.form = angular.copy(response.data);

        // Начинаем грузить чат только если загрузился профиль.
        SeasonService.getMails($stateParams.year).then(function(response) {
          $scope.chat = response.data;
        });
      }, function(response) {
        $scope.form = {};
      });

      /**
       * Написать письмо.
       */
      $scope.sendMail = function(receptient) {
        var year = $scope.season.year;
        if (receptient == 'giftee') {
          var message = $scope.chat.giftee_message;
          $scope.chat.giftee_message = '';
        } else {
          var message = $scope.chat.santa_message;
          $scope.chat.santa_message = '';
        }
        SeasonService.sendMail(year, message, receptient).then(function(response) {
          $scope.chat = response.data;
        });
      };

      /**
       * Отправить подарок.
       */
      $scope.sendGift = function() {
        SeasonService.sendGift($scope.season.year).then(function(response) {
          $scope.member = response.data;
          $scope.season.sent++;
        });
      };

      /**
       * Получить подарок.
       */
      $scope.receiveGift = function() {
        SeasonService.receiveGift($scope.season.year).then(function(response) {
          $scope.member = response.data;
          $scope.season.received++;
        });
      };

      /**
       * Записаться в участники.
       */
      $scope.signUp = function() {
        console.log($scope.form);
        console.log($scope);
        SeasonService.signUp($scope.season.year, $scope.form).then(function(response) {
          $scope.member = response.data;
          $scope.season.members++;
        });
      };

      /**
       * Отказаться от участия.
       */
      $scope.signOut = function() {
        SeasonService.signOut($scope.season.year).then(function() {
          $scope.member = null;
          $scope.season.members--;
        });
      };
    }]);

})(window, window.angular);
